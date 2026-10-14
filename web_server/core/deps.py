from jose import jwt, JWTError
from core.database import get_db
from core.config import settings
from models.user_model import User
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer
from core.exceptions import UnauthorizedException
from fastapi import Depends, HTTPException, status, Request

# This tells FastAPI that tokens will be sent with Authorization: Bearer <token>
# Keeping this for API access if needed, though we focus on cookies now.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Try to get token from cookie if header is missing
    if not token:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
        elif token: # In case we just stored the token string
             pass
    
    if not token:
        raise UnauthorizedException()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub") # type: ignore
        if email is None:
            raise UnauthorizedException()

    except JWTError:
        raise UnauthorizedException()
    
    # Query DB
    user = db.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise UnauthorizedException()

    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_surveillance_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "surveillance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
