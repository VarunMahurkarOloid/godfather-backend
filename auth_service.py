"""
Centralized Authentication Service - Single source of truth for all auth
Uses PyJWT library exclusively for token management
"""
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError
import os
from datetime import datetime, timedelta
from utils.google_client import get_player_by_id
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Single secret key loaded once
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

# HTTP Bearer scheme
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token with expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for player_id: {data.get('player_id')}")
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created refresh token for player_id: {data.get('player_id')}")
    return encoded_jwt

def decode_token(token: str, token_type: str = None) -> Dict:
    """
    Decode and verify JWT token

    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh'). If None, accepts both.

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type if specified (backward compatible - old tokens don't have "type" field)
        if token_type and payload.get("type") and payload.get("type") != token_type:
            logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token type. Expected {token_type} token"
            )

        return payload

    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired. Please login again or refresh your token"
        )
    except (InvalidTokenError, DecodeError) as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

def get_current_user_from_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """Get current user from bearer token - validates access tokens only"""
    token = credentials.credentials
    return decode_token(token, token_type="access")

def refresh_access_token(refresh_token: str) -> str:
    """
    Generate new access token from refresh token

    Args:
        refresh_token: Valid refresh token string

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Decode and validate refresh token
    payload = decode_token(refresh_token, token_type="refresh")

    # Create new access token with same claims (minus exp and type)
    token_data = {
        "player_id": payload.get("player_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "family": payload.get("family")
    }

    new_access_token = create_access_token(token_data)
    logger.info(f"Refreshed access token for player_id: {payload.get('player_id')}")
    return new_access_token

def get_player_from_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """Get full player info from token"""
    payload = get_current_user_from_token(credentials)

    player_id = payload.get("player_id")
    email = payload.get("email")

    # Handle admin/godfather
    admin_email = os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai")
    if player_id == "admin-uuid" or email == admin_email:
        return {
            "player_id": "admin-uuid",
            "email": admin_email,
            "role": "Godfather",
            "family": "Administration",
            "is_admin": True,
            "alive": True,
            "balance": 999999999
        }

    # Get regular player
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player

def verify_admin_from_token(credentials: HTTPAuthorizationCredentials) -> bool:
    """Verify user is admin"""
    payload = get_current_user_from_token(credentials)

    player_id = payload.get("player_id")
    role = payload.get("role", "")

    if player_id == "admin-uuid" or role in ["Godfather", "admin"]:
        return True

    raise HTTPException(status_code=403, detail="Admin access required")

def get_player_id_from_token(credentials: HTTPAuthorizationCredentials) -> str:
    """Extract just the player ID from token"""
    payload = get_current_user_from_token(credentials)
    return payload.get("player_id")
