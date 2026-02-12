from database import SessionLocal, Conversation, Message
from datetime import datetime
import uuid

def create_conversation(user_id, model, title=None):
    db = SessionLocal()
    try:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=title or f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            model=model
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation.id
    finally:
        db.close()

def add_message(conversation_id, role, content):
    """Add a message to a conversation"""
    db = SessionLocal()
    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        
        # Update conversation's updated_at
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now()
        
        db.commit()
        return True
    finally:
        db.close()

# get all messages from a conversation
def get_conversation_history(conversation_id):
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    finally:
        db.close()

# get all conversations
def get_user_conversations(user_id, limit=50):
    db = SessionLocal()
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
        
        return [{
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        } for conv in conversations]
    finally:
        db.close()

def delete_conversation(conversation_id, user_id):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    finally:
        db.close()

def update_conversation_title(conversation_id, user_id, new_title):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if conversation:
            conversation.title = new_title
            conversation.updated_at = datetime.now()
            db.commit()
            return True
        return False
    finally:
        db.close()