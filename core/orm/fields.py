# ---------------
# Field Types
# ---------------

from datetime import datetime, date, time


class Field:

    def __init__(
        self,
        field_type,
        name=None,
        required=False,
        default=None,
        primary_key=False,
        unique=False,
        index=False,
    ):
        self.field_type = field_type
        self.default = default
        self.primary_key = primary_key
        self.required = required
        self.name = name
        self.unique = unique
        self.index = index

    def __repr__(self):
        return f"Field(type={self.field_type}, name={self.name})"


class Integer(Field):
    def __init__(self, **kwargs):
        super().__init__("INTEGER", **kwargs)


class String(Field):
    def __init__(self, size=255, **kwargs):
        super().__init__(f"VARCHAR({size})", **kwargs)


class Boolean(Field):
    def __init__(self, **kwargs):
        super().__init__("BOOLEAN", **kwargs)


class DateTime(Field):
    def __init__(self, **kwargs):
        super().__init__("TIMESTAMP", **kwargs)


class Float(Field):
    def __init__(self, **kwargs):
        super().__init__("REAL", **kwargs)


class Text(Field):
    def __init__(self, **kwargs):
        super().__init__("TEXT", **kwargs)


class Selector(Field):

    def __init__(self, options, name=None, default=None, **kwargs):
        if default is not None and default not in options:
            raise ValueError(f"Default value `{default}` must be in options {options}")
        self.options = options
        super().__init__("VARCHAR(50)", name, **kwargs)

    def validate(self, value):
        if value not in self.options:
            raise ValueError(f"Value `{value}` is not a valid options {self.options}")
