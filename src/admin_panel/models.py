from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, JSON
from src.auth.models import user


metadata = MetaData()

admin_requests = Table(
    "admin_requests",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("timestamp", DateTime),
    Column("info", JSON, nullable=False),
    Column("status", String, nullable=False),
    Column("user_id", Integer, ForeignKey(user.c.id), unique=True),
)
