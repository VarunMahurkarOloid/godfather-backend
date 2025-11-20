from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List

from utils.google_client import get_families, get_all_players

# Import centralized auth
from auth_service import security, get_player_id_from_token

router = APIRouter()

@router.get("/")
async def get_all_families(credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_player_id = get_player_id_from_token(credentials)
    """
    Get all families with their stats
    """
    families = get_families()

    # Sort by total_money or influence_points
    sorted_families = sorted(
        families,
        key=lambda x: float(x.get("total_money", 0)),
        reverse=True
    )

    return {
        "families": sorted_families,
        "total": len(sorted_families)
    }

@router.get("/{family_name}")
async def get_family(family_name: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_player_id = get_player_id_from_token(credentials)
    """
    Get details of a specific family
    """
    families = get_families()
    family = next((f for f in families if f.get("family_name") == family_name), None)

    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return family

@router.get("/{family_name}/members")
async def get_family_members(family_name: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_player_id = get_player_id_from_token(credentials)
    """
    Get all members of a specific family
    """
    players = get_all_players()

    # Filter players by family
    family_members = [
        {
            "player_id": p.get("player_id"),
            "name": p.get("name"),
            "role": p.get("role"),
            "balance": p.get("balance"),
            "individual_score": p.get("individual_score"),
            "missions_completed": p.get("missions_completed"),
            "alive": p.get("alive", True)
        }
        for p in players
        if p.get("family") == family_name
    ]

    if not family_members:
        raise HTTPException(status_code=404, detail="Family not found or has no members")

    # Calculate family stats
    total_money = sum(float(m.get("balance", 0)) for m in family_members)
    total_score = sum(float(m.get("individual_score", 0)) for m in family_members)
    alive_count = sum(1 for m in family_members if m.get("alive", True))

    return {
        "family_name": family_name,
        "members": family_members,
        "total_members": len(family_members),
        "alive_members": alive_count,
        "total_money": total_money,
        "total_score": total_score
    }

@router.get("/leaderboard/top")
async def get_family_leaderboard(limit: int = 10, credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_player_id = get_player_id_from_token(credentials)
    """
    Get top families by total money or influence
    """
    families = get_families()

    # Sort by total_money
    sorted_families = sorted(
        families,
        key=lambda x: float(x.get("total_money", 0)),
        reverse=True
    )[:limit]

    return {
        "families": sorted_families,
        "total": len(sorted_families)
    }

@router.get("/my/family")
async def get_my_family(credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_player_id = get_player_id_from_token(credentials)
    """
    Get current player's family information
    """
    from utils.google_client import get_player_by_id

    player = get_player_by_id(current_player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    family_name = player.get("family")
    if not family_name:
        raise HTTPException(status_code=404, detail="Player has no family assigned")

    # Get family details
    families = get_families()
    family = next((f for f in families if f.get("family_name") == family_name), None)

    # Get family members
    players = get_all_players()
    family_members = [
        {
            "player_id": p.get("player_id"),
            "name": p.get("name"),
            "role": p.get("role"),
            "balance": p.get("balance"),
            "individual_score": p.get("individual_score"),
            "alive": p.get("alive", True)
        }
        for p in players
        if p.get("family") == family_name
    ]

    return {
        "family": family,
        "members": family_members,
        "total_members": len(family_members)
    }
