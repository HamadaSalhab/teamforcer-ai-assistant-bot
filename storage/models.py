# storage/models.py

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from sqlalchemy.engine.base import Engine

engine: Engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    group_id = Column(BigInteger, index=True, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)
    message_content = Column(Text)
    is_bot = Column(Boolean)
    is_group = Column(Boolean)
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)
