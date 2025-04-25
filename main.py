from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
import models
import schemas
import crud
from database import SessionLocal, engine
from auth import create_access_token, get_current_user
import os
from dotenv import load_dotenv

load_dotenv()  
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="User Authentication API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000"), "https://herb-ai.netlify.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
       
@app.get("/")
def read_root():
    return {
        "status": "running",
        "api_version": "1.0.0",
        "documentation": "/docs"
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
   
    access_token = create_access_token(data={"sub": user.username})
   
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
):
    return current_user

@app.get("/admin/dashboard/")
async def admin_dashboard(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return {"message": "Welcome to admin dashboard", "admin": current_user.username}

@app.get("/regular/dashboard/")
async def regular_dashboard(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
):
    return {"message": "Welcome to user dashboard", "user": current_user.username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)