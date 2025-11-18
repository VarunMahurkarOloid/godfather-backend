from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
import os

from utils.google_client import get_player_by_id, get_all_players, update_player, get_news
from utils.scoring import recalculate_player_score

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def get_current_player_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract player ID from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("player_id")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/{player_id}")
async def get_player(player_id: str, current_player_id: str = Depends(get_current_player_id)):
    """
    Get player data by ID
    """
    # Players can only view their own data unless they're admin
    if current_player_id != player_id and current_player_id != "admin-uuid":
        raise HTTPException(status_code=403, detail="Cannot view other player's data")

    player = get_player_by_id(player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Remove password from response
    player_data = {k: v for k, v in player.items() if k != "password"}

    return player_data

@router.get("/me/profile")
async def get_my_profile(current_player_id: str = Depends(get_current_player_id)):
    """
    Get current player's profile
    """
    player = get_player_by_id(current_player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Remove password from response
    player_data = {k: v for k, v in player.items() if k != "password"}

    return player_data

@router.get("/")
async def get_all_players_list(current_player_id: str = Depends(get_current_player_id)):
    """
    Get list of all players (excluding passwords)
    """
    players = get_all_players()

    # Remove passwords and return only basic info
    players_data = [
        {
            "player_id": p.get("player_id"),
            "name": p.get("name"),
            "role": p.get("role"),
            "family": p.get("family"),
            "alive": p.get("alive", True),
            "individual_score": p.get("individual_score", 0)
        }
        for p in players
    ]

    return players_data

class LeaderboardPlayer(BaseModel):
    player_id: int
    name: str
    family: str
    individual_score: float
    money: float
    missions_completed: int
    kills_made: int

@router.get("/leaderboard/top", response_model=List[LeaderboardPlayer])
async def get_leaderboard(limit: int = 10):
    """
    Get top players by individual score
    """
    players = get_all_players()

    # Filter alive players only
    alive_players = [p for p in players if p.get("alive", True)]

    # Sort by individual_score
    sorted_players = sorted(
        alive_players,
        key=lambda x: float(x.get("individual_score", 0)),
        reverse=True
    )[:limit]

    return [
        {
            "player_id": p.get("player_id"),
            "name": p.get("name"),
            "family": p.get("family"),
            "individual_score": float(p.get("individual_score", 0)),
            "money": float(p.get("money", 0)),
            "missions_completed": int(p.get("missions_completed", 0)),
            "kills_made": int(p.get("kills_made", 0))
        }
        for p in sorted_players
    ]

@router.post("/{player_id}/update-score")
async def update_player_score(player_id: str, current_player_id: str = Depends(get_current_player_id)):
    """
    Recalculate and update a player's score
    """
    if current_player_id != "admin-uuid":  # Only admin can manually update scores
        raise HTTPException(status_code=403, detail="Only admin can update scores")

    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    new_score = recalculate_player_score(player)

    update_player(player_id, {"individual_score": new_score})

    return {
        "player_id": player_id,
        "new_score": new_score,
        "message": "Score updated successfully"
    }

@router.get("/news/all")
async def get_all_news(current_player_id: str = Depends(get_current_player_id)):
    """
    Get all news/announcements (public access for all authenticated players)
    """
    news = get_news()

    return {
        "news": news,
        "total": len(news)
    }

@router.post("/me/mark-dead")
async def mark_player_dead(current_player_id: str = Depends(get_current_player_id)):
    """
    Mark the current player as dead
    """
    # Admin cannot be marked as dead
    if current_player_id == "admin-uuid":
        raise HTTPException(status_code=403, detail="Admin cannot be marked as dead")

    player = get_player_by_id(current_player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Update player's alive status to FALSE
    update_player(current_player_id, {"alive": "FALSE"})

    return {
        "success": True,
        "message": "You have been marked as dead. Rest in peace.",
        "player_id": current_player_id
    }
