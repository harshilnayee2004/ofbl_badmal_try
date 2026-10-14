from core.database import get_db
from models.user_model import User
from core.deps import get_admin_user
from sqlmodel import Session, select
from schemas.response_dto import ResponseDTO
from services.user_service import UserService
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.user_dto import UserCreate, UserUpdate, UserResponse

router = APIRouter(
    prefix="/manage-users",
    tags=["Manage Users"],
    dependencies=[Depends(get_admin_user)]
)

@router.post("/", response_model=ResponseDTO)
def create_user(user_dto: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.exec(select(User).where(User.email == user_dto.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    new_user = UserService.create_user(db, user_dto)
    return ResponseDTO(
        status=True,
        message="User created successfully",
        object=UserResponse.model_validate(new_user)
    )

@router.get("/", response_model=ResponseDTO)
def get_all_users(db: Session = Depends(get_db)):
    users = UserService.get_all_users(db)
    return ResponseDTO(
        status=True,
        message="Users fetched successfully",
        object=[UserResponse.model_validate(user) for user in users]
    )

@router.get("/{user_id}", response_model=ResponseDTO)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ResponseDTO(
        status=True,
        message="User fetched successfully",
        object=UserResponse.model_validate(user)
    )

@router.put("/{user_id}", response_model=ResponseDTO)
def update_user(user_id: int, user_dto: UserUpdate, db: Session = Depends(get_db)):
    updated_user = UserService.update_user(db, user_id, user_dto)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ResponseDTO(
        status=True,
        message="User updated successfully",
        object=UserResponse.model_validate(updated_user)
    )

@router.delete("/{user_id}", response_model=ResponseDTO)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ResponseDTO(
        status=True,
        message="User deleted successfully",
        object=None
    )

