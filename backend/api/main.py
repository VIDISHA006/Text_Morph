from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List
from backend.api.database import create_connection
from backend.api.passhash import hash_password, verify_password
from backend.api.auth import create_access_token, verify_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(title="Text Morph AI - Railway")
security = HTTPBearer()

# Simple models for auth
class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    language_preference: str = "English"

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    from backend.api.database import create_users_table, create_profiles_table, create_processing_history_table
    create_users_table()
    create_profiles_table()
    create_processing_history_table()

# Simple auth endpoints
@app.post("/auth/login")
def login(user_data: UserLogin):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, email, hashed_password FROM users WHERE email = %s", (user_data.email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not user or not verify_password(user_data.password, user[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user_data.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user[0],
            "username": user[1],
            "email": user[2]
        }
    }

@app.post("/auth/register")
def register(user_data: UserCreate):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = connection.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (user_data.email, user_data.username))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, language_preference) VALUES (%s, %s, %s, %s)",
        (user_data.username, user_data.email, hashed_password, user_data.language_preference)
    )
    connection.commit()
    
    user_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO profiles (user_id, language_preference) VALUES (%s, %s)",
        (user_id, user_data.language_preference)
    )
    connection.commit()
    cursor.close()
    connection.close()
    
    return {"message": "User registered successfully"}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Text Morph AI is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "text-morph-ai"}

# Simple text processing endpoint
@app.post("/process")
def process_text(text_input: dict):
    text = text_input.get("text", "")
    # Simple text processing without heavy AI libraries
    return {
        "original": text,
        "processed": f"Processed: {text}",
        "length": len(text),
        "words": len(text.split())
    }

# Helper function to get current user from token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"id": user[0], "username": user[1], "email": user[2]}

# History models
class HistoryCreate(BaseModel):
    original_text: str
    processed_text: str
    processing_type: str  # 'summary' or 'paraphrase'
    model_used: str = ""

class HistoryResponse(BaseModel):
    id: int
    user_id: int
    original_text: str
    processed_text: str
    processing_type: str
    model_used: str
    created_at: str

# History endpoints
@app.post("/history/save", status_code=201)
def save_history(history_data: HistoryCreate, current_user: dict = Depends(get_current_user)):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = connection.cursor()
    cursor.execute(
        """INSERT INTO processing_history (user_id, original_text, processed_text, processing_type, model_used) 
           VALUES (%s, %s, %s, %s, %s)""",
        (current_user["id"], history_data.original_text, history_data.processed_text, 
         history_data.processing_type, history_data.model_used)
    )
    connection.commit()
    
    # Get the inserted ID
    history_id = cursor.lastrowid
    cursor.close()
    connection.close()
    
    return {"id": history_id, "message": "History saved successfully"}

@app.get("/history/user/{user_id}")
def get_user_history(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's history")
    
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = connection.cursor()
    cursor.execute(
        """SELECT id, user_id, original_text, processed_text, processing_type, model_used, created_at 
           FROM processing_history WHERE user_id = %s ORDER BY created_at DESC""",
        (user_id,)
    )
    history = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return [
        {
            "id": h[0],
            "user_id": h[1],
            "original_text": h[2],
            "processed_text": h[3],
            "processing_type": h[4],
            "model_used": h[5],
            "created_at": str(h[6])
        }
        for h in history
    ]

# Verification endpoint (optional)
@app.get("/verify")
def verify_token_endpoint():
    return {"message": "Verification endpoint available"}