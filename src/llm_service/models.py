from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, JSON, Numeric, Boolean
from src.auth.models import user

metadata = MetaData()

request_statistic = Table(
    "request_statistic",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey(user.c.id)),
    Column("received_at", DateTime),
    Column("operation", String, nullable=False),
    Column("prompt_path", String, nullable=False),
    Column("doc_name", String, nullable=True),
    Column("tokens", Integer, nullable=False),
    Column("total_time", Numeric(precision=10, scale=3), nullable=False),
    Column("gigachat_time", Numeric(precision=10, scale=3)),
)

feedback = Table(
    "feedback",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("value", String),
    Column("user_comment", String, nullable=True),
    Column("request_id", Integer, ForeignKey(request_statistic.c.id)),
)

test_system = Table(
    "test_system",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("request_id", Integer, ForeignKey(request_statistic.c.id)),
    Column("question", String, nullable=False),
    Column("option_1", String, nullable=False),
    Column("option_2", String, nullable=False),
    Column("option_3", String, nullable=False),
    Column("option_4", String, nullable=False),
    Column("right_answer", String, nullable=False),
    Column("answered_at", DateTime, nullable=True, default=None),
)


answer_question_system = Table(
    "answer_question_system",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("request_id", Integer, ForeignKey(request_statistic.c.id)),
    Column("question", String, nullable=False),
    Column("answer", String, nullable=False),
    Column("metrics", JSON, nullable=False),
)

contest = Table(
    "contest",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey(user.c.id)),
    Column("doc_name", String, nullable=False),
    Column("total_tests", Integer, nullable=False),
    Column("points", Numeric(precision=4, scale=1), nullable=False)
)
