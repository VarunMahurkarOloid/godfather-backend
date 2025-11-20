"""
Centralized authentication utilities for JWT token verification
"""
from fastapi import HTTPException, Header
from typing import Optional
import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify JWT token, return user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        print(f"[AUTH ERROR] JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_player(authorization: Optional[str] = Header(None)):
    """Extract player info from JWT token - compatible with existing code"""
    from utils.google_client import get_player_by_id

    payload = get_current_user(authorization)
    player_id = payload.get("player_id")
    email = payload.get("email")

    # Handle admin/godfather
    if player_id == "admin-uuid" or email == "godfather" or email == os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai"):
        return {
            "player_id": "admin-uuid",
            "email": os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai"),
            "role": "Godfather",
            "family": "Administration",
            "is_admin": True
        }

    # Get full player data by UUID
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player

def get_current_player_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract player ID from JWT token"""
    payload = get_current_user(authorization)
    return payload.get("player_id")

def verify_admin(authorization: Optional[str] = Header(None)) -> bool:
    """Verify that the request is from an admin"""
    payload = get_current_user(authorization)

    # Check if user is admin
    player_id = payload.get("player_id")
    role = payload.get("role", "")

    if player_id == "admin-uuid" or player_id == 0 or role in ["Godfather", "admin"]:
        return True

    raise HTTPException(status_code=403, detail="Admin access required")
