from sqlmodel import Session, select
from models.user_model import User
from core.security import verify_password, hash_password
from schemas.user_dto import UserCreate, UserUpdate
from typing import List, Optional
class UserService:

    @staticmethod
    def check_user():
        print("Hello world")

    @staticmethod
    def authenticate_user(db: Session, email, password):
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        hashed_pwd = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password=hashed_pwd,
            role=user_data.role,
            status=user_data.status
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        return db.exec(select(User).where(User.role != 'admin')).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.exec(select(User).where(User.id == user_id)).first()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        if 'password' in update_data and update_data['password']:
            update_data['password'] = hash_password(update_data['password'])
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            return False
        
        user.password = hash_password(new_password)
        db.commit()
        return True