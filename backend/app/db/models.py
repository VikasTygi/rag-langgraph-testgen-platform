from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Generation(Base):
    __tablename__ = "generations"

    generation_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)

    framework = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)

    status = Column(String, index=True, nullable=False)

    result_url = Column(String, nullable=True)
    result_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))