import os
import requests
from fastapi import HTTPException, Request, Cookie
from typing import Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import User, UserSession
from fastapi import HTTPException


EMERGENT_AUTH_API = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


async def process_session_id(session_id: str, db: AsyncIOMotorDatabase | None):
    """Process session_id from Emergent OAuth and create user session."""
    try:
        # Call Emergent auth API to get user data
        headers = {"X-Session-ID": session_id}
        response = requests.get(EMERGENT_AUTH_API, headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        
        # Check if user exists
        existing_user = await db.users.find_one({"_id": user_data["id"]})
        
        if not existing_user:
            # Create new user
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture")
            )
            await db.users.insert_one({"_id": user.id, **user.dict(exclude={"id"})})
        
        # Create session
        session_token = user_data["session_token"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session = UserSession(
            user_id=user_data["id"],
            session_token=session_token,
            expires_at=expires_at
        )
        
        # Delete old sessions for this user
        await db.user_sessions.delete_many({"user_id": user_data["id"]})
        
        # Insert new session
        await db.user_sessions.insert_one(session.dict())
        
        return {"session_token": session_token, "user": user_data}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Session processing failed: {str(e)}")


async def get_current_user(request: Request, db: AsyncIOMotorDatabase, session_token: Optional[str] = Cookie(None)):
    """Get current user from session token (cookie or Authorization header)."""
    
    # Try cookie first
    token = session_token
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    if session["expires_at"] < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": token})
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_doc = await db.users.find_one({"_id": session["user_id"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Map _id to id
    user_doc["id"] = user_doc.pop("_id")
    return User(**user_doc)
