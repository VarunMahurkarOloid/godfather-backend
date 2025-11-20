from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
import os
import uuid

from utils.google_client import (
    get_player_by_email,
    update_player_by_email,
    get_player_by_id,
    update_score
)

# Import centralized auth functions
from auth_service import (
    create_access_token,
    create_refresh_token,
    refresh_access_token,
    decode_token
)

router = APIRouter()

class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None  # Backward compatibility
    password: str
    role: Optional[str] = None  # Role selection for first-time login

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    player: dict
    is_first_login: bool = False
    assigned_role: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user with email and password
    - First login: User must select their assigned role, UUID is generated
    - Subsequent logins: Role is verified against stored role
    """
    # Get email from either field (backward compatibility)
    user_email = request.email or request.username

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username is required"
        )

    # Admin login shortcut
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "godfatheradmin@12345varun")

    if user_email == ADMIN_USERNAME:
        if request.password != ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )

        # Validate admin must select Godfather role
        if request.role and request.role != "Godfather":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin must login with 'Godfather' role"
            )

        token_data = {
            "player_id": "admin-uuid",
            "email": ADMIN_USERNAME,
            "role": "Godfather"
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        admin_player = {
            "player_id": "admin-uuid",
            "name": "Varun Mahurkar (Godfather)",
            "email": ADMIN_USERNAME,
            "role": "Godfather",
            "family": "Administration",
            "balance": 999999999,
            "alive": True,
            "is_admin": True
        }

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "player": admin_player,
            "is_first_login": False
        }

    # Get player from database by email
    player = get_player_by_email(user_email)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    # Check password
    if player.get("password") != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if player is alive
    if player.get("alive") == "FALSE" or not player.get("alive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your character has been eliminated from the game"
        )

    # Check if player has been assigned a family and role by admin
    assigned_role = player.get("assigned_role", "")
    assigned_family = player.get("family", "")

    if not assigned_role or assigned_role == "":
        # Player not yet assigned by admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval. Please contact the admin to assign you a family and role."
        )

    # Check if this is first login (no player_id/UUID assigned)
    if not player.get("player_id") or player.get("player_id") == "":
        # First time login - need role selection
        if not request.role:
            # Return assigned role info - frontend should prompt for role selection
            return {
                "access_token": "",
                "token_type": "bearer",
                "player": {},
                "is_first_login": True,
                "assigned_role": assigned_role
            }

        # Verify selected role matches assigned role
        if request.role != assigned_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are assigned the role '{assigned_role}'. Please select the correct role."
            )

        # Generate UUID and update player - set role from assigned_role
        new_uuid = str(uuid.uuid4())
        update_player_by_email(user_email, {
            "player_id": new_uuid,
            "role": assigned_role,
            "registered": "TRUE"
        })

        # Update scorecard with UUID
        update_score(new_uuid, {
            "player_id": new_uuid,
            "role": assigned_role
        })

        # Refresh player data
        player = get_player_by_email(user_email)

    else:
        # Returning user - must verify role
        stored_role = player.get("role", "")

        # Require role for all logins
        if not request.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role selection is required for login"
            )

        # Validate role matches stored role (unconditional)
        if request.role != stored_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role mismatch. You are registered as '{stored_role}'. Please select the correct role."
            )

    # Create both access and refresh tokens with UUID, email, role, and family
    token_data = {
        "player_id": player["player_id"],
        "email": player.get("email") or user_email,
        "role": player.get("role"),
        "family": player.get("family")
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Remove password from response
    player_data = {k: v for k, v in player.items() if k != "password"}

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "player": player_data,
        "is_first_login": False
    }

@router.get("/verify")
async def verify_token(token: str):
    """
    Verify if a token is valid and return player info
    """
    try:
        payload = decode_token(token)
        player_id = payload.get("player_id")

        # Get current player data
        if player_id and player_id != "admin-uuid":
            player = get_player_by_id(player_id)
            if player:
                # Remove password from response
                player_data = {k: v for k, v in player.items() if k != "password"}
                return {
                    "valid": True,
                    "player": player_data
                }

        return {"valid": True, "player_id": player_id}
    except HTTPException:
        # Re-raise HTTPException from decode_token
        raise

@router.post("/refresh", response_model=RefreshResponse)
async def refresh(request: RefreshRequest):
    """
    Refresh access token using a valid refresh token

    Args:
        request: RefreshRequest containing refresh_token

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        new_access_token = refresh_access_token(request.refresh_token)
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        # Re-raise HTTPException from refresh_access_token
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {str(e)}"
        )
