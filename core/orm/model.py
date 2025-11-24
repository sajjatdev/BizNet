# ---------------------------
# Meta class to collect fields
# ---------------------------

from core.orm import fields
from core.db import db
from datetime import datetime


class ModelMeta(type):
    """
    Metaclass responsible for collecting all field definitions declared
    on the model class and preparing ORM-related metadata.

    Responsibilities:
    -----------------
    - Collect fields from parent classes (inheritance).
    - Collect fields defined in the current class.
    - Automatically generate human-readable titles for unnamed fields.
    - Normalize and determine the database table name.
    """

    def __new__(cls, name, bases, attrs):
        # ---------------------------
        # 1. Collect inherited fields
        # ---------------------------
        fields_dist = {}

        for base in bases:
            if hasattr(base, "_fields"):
                fields_dist.update(base._fields)

        # ---------------------------
        # 2. Collect fields from this class
        # ---------------------------
        for key, value in attrs.items():
            if isinstance(value, fields.Field):
                fields_dist[key] = value

                # Auto-fill field label/title if not provided
                if value.name is None:
                    value.name = str(key).replace("_", " ").title()

        # Store collected fields in class attributes
        attrs["_fields"] = fields_dist

        # ---------------------------
        # 3. Determine table name
        # ---------------------------
        model_name = attrs.get("_name", None)

        if model_name:
            # Convert dot-notation model name → table name
            # Example: "res.user" → "res_user"
            table_name = str(model_name).replace(".", "_").lower().strip()
        else:
            # Default to class name
            table_name = name

        # Attach metadata
        attrs["_name"] = model_name
        attrs["_table"] = table_name

        return super().__new__(cls, name, bases, attrs)


class BaseModel(metaclass=ModelMeta):
    """
    Base ORM class for all models.
    Provides:
    ---------
    - Automatic field binding
    - Pretty repr()
    - SQL table creation method
    """

    _name: str = ""  # Should be overridden by subclasses

    # ------------------------------------------------------------
    # Default system fields
    # ------------------------------------------------------------
    id = fields.Integer(name="id", primary_key=True)
    created_at = fields.DateTime(name="created_at")
    updated_at = fields.DateTime(name="updated_at")

    def __init__(self, **kwargs):
        """
        Initialize model record with provided keyword values.
        """
        for field_name in self._fields:
            value = kwargs.get(field_name, None)
            setattr(self, field_name, value)

    def __repr__(self):
        """
        Developer-friendly representation of the model instance.
        Example:
            User(id=1, name="John", is_active=True)
        """
        field_values = " , ".join(f"{k}={getattr(self, k)}" for k in self._fields)
        return f"{self.__class__.__name__}({field_values})"

    # ------------------------------------------------------------
    # Database Table Creation
    # ------------------------------------------------------------
    @classmethod
    def create_table(self):
        """
        Auto-generate CREATE TABLE and auto-migrate missing columns.
        """

        table = self._table

        # STEP 1: Ensure table exists (empty table with id)
        db.Database.execute(
            f"CREATE TABLE IF NOT EXISTS {table} (id SERIAL PRIMARY KEY);"
        )

        # STEP 2: Get existing columns from PostgreSQL
        existing_columns = db.Database.execute(
            """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                """,
            (table,),
        )

        existing_columns = {col[0] for col in existing_columns}

        # STEP 3: Loop through fields and add missing ones
        for field_name, field in self._fields.items():

            # Skip if field already exists
            if field_name in existing_columns:
                continue

            # -----------------------------
            # Build COLUMN SQL Definition
            # -----------------------------
            if field.primary_key:
                # Primary key already created above
                continue

            # 1. Selector Field → VARCHAR + CHECK
            if isinstance(field, fields.Selector):
                allowed_values = tuple(str(opt[0]).lower() for opt in field.options)
                default_val = field.default or allowed_values[0]

                col_def = (
                    f"{field_name} {field.field_type} "
                    f"DEFAULT '{default_val}' "
                    f"CHECK ({field_name} IN {allowed_values})"
                )

            # 2. Other fields
            else:
                col_def = f"{field_name} {field.field_type}"

                # Unique
                if getattr(field, "unique", False):
                    col_def += " UNIQUE"

                # Required
                if getattr(field, "required", False):
                    col_def += " NOT NULL"

                # Default
                if field.default is not None:
                    col_def += f" DEFAULT '{field.default}'"

                # Auto timestamps
                if isinstance(field, fields.DateTime) and field_name in (
                    "created_at",
                    "updated_at",
                ):
                    col_def += " DEFAULT CURRENT_TIMESTAMP"

            # STEP 4: Alter table add column
            alter_sql = f"ALTER TABLE {table} ADD COLUMN {col_def};"

            db.Database.execute(alter_sql)
