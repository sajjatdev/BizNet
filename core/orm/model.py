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
        Auto-generate SQL CREATE TABLE statement based on model fields.

        Example Output:
        ----------------
        CREATE TABLE IF NOT EXISTS res_user (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        columns = []

        for field_name, field in self._fields.items():

            # Primary key field
            col_def = (
                f"{field_name} SERIAL PRIMARY KEY"
                if field.primary_key
                else f"{field_name} {field.field_type}"
            )

            # Unique constraint
            if field.unique and not field.primary_key:
                col_def += " UNIQUE"

            # NOT NULL constraint
            if field.required:
                col_def += " NOT NULL"

            # Default value constraint
            if field.default:
                col_def += f" DEFAULT {field.default}"

            # Selector value constraint

            # System fields are auto timestamped
            if isinstance(field, fields.DateTime) and field_name in [
                "created_at",
                "updated_at",
            ]:
                col_def += " DEFAULT CURRENT_TIMESTAMP"

            columns.append(col_def)

        query = f"CREATE TABLE IF NOT EXISTS {self._table} ({', '.join(columns)});"

        # Execute table creation query
        db.Database.execute(query)
