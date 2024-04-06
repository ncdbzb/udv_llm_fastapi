from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, JSON, Numeric

metadata = MetaData()

request_statistic = Table(
    "request_statistic",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("timestamp", DateTime),
    Column("operation", String, nullable=False),
    Column("prompt_path", String, nullable=False),
    Column("tokens", Integer, nullable=False),
    Column("total_time", Numeric(precision=10, scale=3), nullable=False),
    Column("metrics", JSON, nullable=True),
    Column("gigachat_time", Numeric(precision=10, scale=3)),
)

feedback = Table(
    "feedback",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("value", String),
    Column("llm_response", String, nullable=False),
    Column("user_comment", String, nullable=True),
    Column("request_id", Integer, ForeignKey(request_statistic.c.id)),
)
