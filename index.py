from core.orm import fields, model
from core.db import db


class User(model.BaseModel):

    _name: str = "res.user"

    username = fields.String(name="username", required=True, size=100, index=True)
    email = fields.String(name="email", size=255, unique=True, index=True)
    is_active = fields.Boolean(name="is_active", default=True)
    status = fields.Selector(options=[("pendding", "Pending")])


db.Database.connect(dbname="orm_test_db", user="test_user", password="123456")
User.create_table()
