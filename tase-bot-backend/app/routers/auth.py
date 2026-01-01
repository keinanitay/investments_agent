from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.db.database import get_database
from app.db import repository
from app.models.schemas import UserCreate, UserInDB, UserUpdate
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

router = APIRouter()

# setup hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# jwt configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") ##### change this default 'supersecretkey' key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

def verify_password(plain_password, hashed_password):
    """verifies a plain password against the hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """returns the bcrypt hash of a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """generates a jwt access token with expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_database)):
    """dependency to validate the token and retrieve the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await repository.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return user

@router.post("/signup")
async def signup(user: UserCreate, db = Depends(get_database)):
    """registers a new user and returns an access token."""
    existing_user = await repository.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.model_dump()
    user_dict["created_at"] = datetime.utcnow()
    
    # hash the password
    user_dict["password"] = get_password_hash(user_dict["password"])
    
    user_id = await repository.create_user(db, user_dict)
    user_dict["_id"] = user_id
    
    # generate token for auto-login
    access_token = create_access_token(data={"sub": user_dict["email"]})
    
    # remove password from response
    user_dict.pop("password", None)
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_dict}

@router.post("/login")
async def login(auth_data: dict, db = Depends(get_database)):
    """authenticates a user and returns an access token."""
    email = auth_data.get("email")
    password = auth_data.get("password")
    
    user = await repository.get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # verify the hash
    if not verify_password(password, user.get("password")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user["_id"] = str(user["_id"])
    
    # generate token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.put("/profile", response_model=UserInDB)
async def update_profile(payload: UserUpdate, current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """updates the current user's profile settings."""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    
    user_id = current_user["_id"]
    if update_data:
        success = await repository.update_user(db, user_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="User not found or invalid ID")
        
    user = await repository.get_user_by_id(db, user_id)
    user["_id"] = str(user["_id"])
    return user

@router.delete("/profile")
async def delete_user(current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """permanently deletes the current user account."""
    await repository.delete_user(db, current_user["_id"])
    return {"status": "deleted"}