# storage/sqlalchemy_database.py

from sqlalchemy.orm import Session
from .models import ChatHistory, SessionLocal
from datetime import datetime
# from .models import Base
# from config import DATABASE_URL
# from sqlalchemy import create_engine, inspect, text

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def drop_and_recreate_table():
#     # Create engine and session
#     engine = create_engine(DATABASE_URL)
#     SessionLocal.configure(bind=engine)
#     session = SessionLocal()

#     # Drop the table if it exists
#     session.execute(text('DROP TABLE IF EXISTS chat_history'))
#     session.commit()
#     print("Table 'chat_history' has been dropped.")

#     # Recreate the table with the updated schema
#     Base.metadata.create_all(bind=engine)
#     print("Table 'chat_history' has been recreated with the updated schema.")

#     # Verify the new schema
#     inspector = inspect(engine)
#     columns = [column['name'] for column in inspector.get_columns('chat_history')]
#     print("New schema columns for 'chat_history':", columns)

def save_message(db: Session, user_id: int, group_id: int, is_bot: bool, message_content: str, is_group: bool, file_name: str = None, file_type: str = None):  
    current_time = datetime.utcnow()  # Get current UTC time
    db_message = ChatHistory(
        user_id=user_id,
        group_id=group_id,
        message_content=message_content,
        is_group=is_group,
        is_bot=is_bot,
        timestamp=current_time,
        file_name=file_name,
        file_type=file_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    print(f"Saved message: user_id={db_message.user_id}, group_id={db_message.group_id}, "
          f"timestamp={db_message.timestamp}, is_group={db_message.is_group}, "
          f"content='{message_content}', file_name='{file_name}', file_type='{file_type}'")
    return db_message

def get_chat_history(db: Session, user_id: int = None, group_id: int = None) -> ChatHistory:
    if group_id:
        return db.query(ChatHistory).filter(ChatHistory.group_id == group_id).order_by(ChatHistory.timestamp).all()
    elif user_id:
        return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.timestamp).all()
    else:
        return db.query(ChatHistory).order_by(ChatHistory.timestamp).all()