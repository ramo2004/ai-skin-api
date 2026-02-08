import firebase_admin
from firebase_admin import auth as firebase_auth
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Header
from typing import Optional
from gpt_service import classify_image
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv(".env")

# Initialize Firebase Admin
# Note: In production, pass credentials from a service account JSON file
# For token verification only, initialize_app() is often sufficient if project ID can be inferred
try:
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    if firebase_project_id:
        firebase_admin.initialize_app(options={"projectId": firebase_project_id})
    else:
        firebase_admin.initialize_app()
except ValueError:
    # Already initialized
    pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split("Bearer ")[1]
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.post("/classify/")
async def classify(
    file: UploadFile = File(...),
    age: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    skin_type: Optional[str] = Form(None),
    scan_type: str = Form("face"), # Default to face for backward compatibility
    user: dict = Depends(get_current_user)
):
    contents = await file.read()
    
    # Common User Context
    user_context = {
        "age": age,
        "gender": gender,
        "skin_type": skin_type
    }
    
    # Route based on scan_type
    if scan_type == "product":
        from gpt_service import analyze_ingredients
        result = await analyze_ingredients(contents, file.filename, user_context)
        return {"type": "product", "result": result}
    
    try:
        result = await classify_image(contents, file.filename, user_context)
        return {"type": "face", "classification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
