from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, ForeignKey
from src.auth.models import user


metadata = MetaData()

doc = Table(
    "doc",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, unique=True, nullable=False),
    Column("type", String, nullable=True),
    Column("chunk_size", Integer, nullable=True),
    Column("embedding_model", String, nullable=True),
    Column("description", String, nullable=False),
    Column("user_id", Integer, ForeignKey(user.c.id)),
    Column("in_contest", Boolean, nullable=True, default=False),
)
