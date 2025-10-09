from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Import routers
from backend.api.routers.auth_routes import router as auth_router
from backend.api.routers.profile_routes import router as profile_router
from backend.paraphrasing.router import router as paraphrasing_router
from backend.api.history import router as history_router
from backend.api.database import create_admin_table, create_users_table, create_profiles_table, create_user_texts_table, create_processing_history_table, create_admin_activity_table, create_user_feedback_table

app = FastAPI()
app = FastAPI(title="Text Morph API")

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    create_users_table()
    create_profiles_table()
    create_user_texts_table()
    create_processing_history_table()
    create_admin_table()
    create_admin_activity_table()
    create_user_feedback_table()

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(paraphrasing_router, prefix="/paraphrasing", tags=["paraphrasing"])
app.include_router(history_router, tags=["history"])

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

security = HTTPBearer()

@app.get("/verify")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    from backend.api.auth import verify_token
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email}

