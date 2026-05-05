from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import random
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from model import model_instance
from database import create_user, get_user_by_username, username_exists, update_user, update_password

# Security Configuration
SECRET_KEY = "zenith-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Zenith API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for testing
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UsageData(BaseModel):
    screen_time: float
    app_switches: int
    hour: Optional[int] = None

class PredictionResponse(BaseModel):
    focus_score: float
    insight: str

class ChatMessage(BaseModel):
    message: str

class Insight(BaseModel):
    id: str
    type: str
    message: str
    riskScore: Optional[str] = None
    time: str
    color: str

# --- Database is now handled by database.py (SQLite) ---

# --- Security Helpers ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Ensure we are hashing a string and not some complex object
    if not isinstance(password, str):
        password = str(password)
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user_data = get_user_by_username(username)
    if user_data is None:
        raise credentials_exception
    return User(username=user_data["username"], email=user_data["email"], full_name=user_data["full_name"])

# --- Auth Endpoints ---

@app.post("/register", response_model=User)
async def register(user_in: UserCreate):
    if username_exists(user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    try:
        hashed_password = get_password_hash(str(user_in.password))
        user_data = create_user(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password
        )
        print(f"[Zenith] User '{user_in.username}' registered successfully")
        return User(**user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Zenith] Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = get_user_by_username(form_data.username)
    if not user_data or not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user_data["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

class ProfileUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@app.put("/users/me", response_model=User)
async def update_profile(profile: ProfileUpdate, current_user: User = Depends(get_current_user)):
    updated = update_user(
        username=current_user.username,
        email=profile.email,
        full_name=profile.full_name
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return User(username=updated["username"], email=updated["email"], full_name=updated["full_name"])

@app.post("/users/me/password")
async def change_password(data: PasswordChange, current_user: User = Depends(get_current_user)):
    user_data = get_user_by_username(current_user.username)
    if not user_data or not verify_password(data.current_password, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = get_password_hash(str(data.new_password))
    update_password(current_user.username, new_hash)
    return {"message": "Password updated successfully"}

# --- App Endpoints ---

@app.get("/")
async def root():
    return {"message": "Welcome to Zenith API"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_focus(data: UsageData, current_user: User = Depends(get_current_user)):
    current_hour = data.hour if data.hour is not None else datetime.now().hour
    score = model_instance.predict_focus_score(data.screen_time, data.app_switches, current_hour)
    
    if score > 80:
        insight = "You are in a high focus state! Perfect time for complex tasks."
    elif score > 60:
        insight = "Decent focus levels. Consider a 5-minute breather to maintain performance."
    else:
        insight = "Focus score is low. We recommend a 15-minute screen break to recharge."
        
    return {
        "focus_score": score,
        "insight": insight
    }

@app.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    return [
        {"title": "Screen Time", "value": "4h 12m", "trend": "+12%", "trendUp": False},
        {"title": "Focus Score", "value": str(random.randint(70, 95)), "trend": "+5", "trendUp": True},
        {"title": "Active Blocks", "value": "12", "trend": "-2", "trendUp": True},
        {"title": "Energy Level", "value": "High", "trend": "Stable", "trendUp": True},
    ]

@app.get("/insights", response_model=List[Insight])
async def get_insights(current_user: User = Depends(get_current_user)):
    return [
        {
            "id": "1",
            "type": "warning",
            "message": "Your social media usage has increased by 40% in the last 3 days. Consider scheduling specific blocks for checking feeds.",
            "riskScore": "High",
            "time": "2 hours ago",
            "color": "destructive"
        },
        {
            "id": "2",
            "type": "achievement",
            "message": "Great job! You've maintained your Deep Work goals for 4 consecutive days.",
            "time": "5 hours ago",
            "color": "primary"
        },
        {
            "id": "3",
            "type": "tip",
            "message": "You often lose focus around 3 PM. Most users find a 15-minute screen-free break at this time re-energizes them.",
            "riskScore": "Low",
            "time": "Yesterday",
            "color": "secondary"
        }
    ]

@app.post("/chat")
async def chat_with_ai(msg: ChatMessage, current_user: User = Depends(get_current_user)):
    responses = [
        "Based on your usage today, I suggest a 5-minute breathing exercise now.",
        "Your focus score is excellent! You've managed to stay in 'Deep Work' for 2 hours.",
        "Detected frequent app switching. Shall I activate your 'Social Media' blocklist for the next hour?",
        "You're making great progress on your digital wellness goals today.",
        "Taking a short 10-minute walk could help clear your mind and boost your focus score.",
    ]
    return {"response": random.choice(responses)}

if __name__ == "__main__":
    import uvicorn
    # Using module string for reliability with reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
