from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_db
from models.user_model import User
from models.message_model import Message
from core.deps import get_current_user
from schemas.message_dto import SendMessagePayload
from schemas.response_dto import ResponseDTO
from socket_controller.chat_socket_controller import chat_manager

router = APIRouter(
    prefix="/chat",
    tags=["Chat API"]
)

@router.get("/history")
def get_chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch global chat history with sender details."""
    statement = select(Message, User.email).join(User, Message.sender_id == User.id)
    
    # Filter restricted messages for surveillance users
    if current_user.role == "surveillance":
        statement = statement.where(Message.restricted_from_surveillance == False)
        
    statement = statement.order_by(Message.timestamp)
    
    results = db.exec(statement).all()
    
    history = []
    for msg, sender_email in results:
        msg_dict = msg.dict()
        msg_dict["sender_email"] = sender_email
        history.append(msg_dict)
        
    return ResponseDTO(message="Global chat history fetched", status=True, object=history)

@router.post("/send")
async def send_message(
    payload: SendMessagePayload, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Admin/Surveillance sends global message to all Users."""
    if current_user.role not in ["admin", "surveillance"]:
        raise HTTPException(status_code=403, detail="Unidirectional chat: only admin/surveillance can send messages")
        
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=None,
        content=payload.content,
        restricted_from_surveillance=payload.restricted_from_surveillance
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    message_data = {
        "id": db_message.id,
        "sender_id": db_message.sender_id,
        "sender_email": current_user.email,
        "receiver_id": db_message.receiver_id,
        "content": db_message.content,
        "restricted_from_surveillance": db_message.restricted_from_surveillance,
        "timestamp": db_message.timestamp.isoformat(),
        "is_read": db_message.is_read
    }
    
    # Broadcast to websocket connections
    await chat_manager.broadcast(
        {"type": "new_message", "message": message_data},
        exclude_role="surveillance" if payload.restricted_from_surveillance else None
    )
    
    return ResponseDTO(message="Global message sent successfully", status=True, object=message_data)
