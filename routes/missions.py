from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import os

from utils.google_client import (
    get_missions_for_player, get_all_missions, update_mission,
    get_player_by_id, update_player, is_admin, update_score
)
from utils.scoring import recalculate_player_score
from auth_service import security, get_player_from_token

router = APIRouter()

@router.get("/today")
async def get_today_missions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    player = get_player_from_token(credentials)
    """
    Get today's missions for the current player (role-based filtering)
    Missions unlock at 9 AM based on the game day
    """
    from datetime import datetime
    import pytz

    # Check if admin - they see everything regardless of time
    admin_access = is_admin(player.get("email"))

    # Get current game day from admin settings
    import sys
    sys.path.append(".")
    from routes.admin import game_state

    current_day = game_state.get("current_day", 1)
    mission_unlock_hour = game_state.get("mission_unlock_hour", 9)

    # Check if missions are unlocked (after 9 AM)
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_hour = current_time.hour

    missions_unlocked = current_hour >= mission_unlock_hour or admin_access

    if not missions_unlocked:
        return {
            "day": current_day,
            "missions": [],
            "total": 0,
            "player_role": player.get("role"),
            "player_family": player.get("family"),
            "admin_view": admin_access,
            "unlocked": False,
            "unlock_time": f"{mission_unlock_hour}:00 AM",
            "message": f"New missions will unlock at {mission_unlock_hour}:00 AM IST. Stay tuned!"
        }

    # Get missions visible to this player
    missions = get_missions_for_player(
        player_id=player.get("player_id"),
        role=player.get("role"),
        family=player.get("family"),
        is_admin=admin_access
    )

    # Debug logging
    print(f"[DEBUG] Current game day: {current_day}")
    print(f"[DEBUG] Total missions before filtering: {len(missions)}")
    if missions:
        print(f"[DEBUG] Sample mission days: {[m.get('day') for m in missions[:5]]}")

    # Filter by current day - everyone sees only current day missions
    today_missions = [m for m in missions if m.get("day") == current_day]

    print(f"[DEBUG] Missions after day filter: {len(today_missions)}")

    return {
        "day": current_day,
        "missions": today_missions,
        "total": len(today_missions),
        "player_role": player.get("role"),
        "player_family": player.get("family"),
        "admin_view": admin_access,
        "unlocked": True,
        "unlock_time": f"{mission_unlock_hour}:00 AM"
    }

@router.get("/all")
async def get_all_missions_for_player(
    day: Optional[int] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    player = get_player_from_token(credentials)
    """
    Get all missions visible to current player (filtered by role/family and current game day)
    """
    from routes.admin import game_state

    admin_access = is_admin(player.get("email"))

    missions = get_missions_for_player(
        player_id=player.get("player_id"),
        role=player.get("role"),
        family=player.get("family"),
        is_admin=admin_access
    )

    # Filter by current game day (unless a specific day is requested)
    if day is not None:
        missions = [m for m in missions if m.get("day") == day]
    else:
        # Filter by current game day from game_state
        current_day = game_state.get("current_day", 1)
        missions = [m for m in missions if m.get("day") == current_day]

    return {
        "missions": missions,
        "total": len(missions),
        "filtered_by": "admin" if admin_access else f"role={player.get('role')}, family={player.get('family')}",
        "current_day": game_state.get("current_day", 1)
    }

@router.get("/{mission_id}")
async def get_mission(mission_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    player = get_player_from_token(credentials)
    """
    Get a specific mission by ID (if player has access)
    """
    admin_access = is_admin(player.get("email"))

    # Get all missions visible to player
    missions = get_missions_for_player(
        player_id=player.get("player_id"),
        role=player.get("role"),
        family=player.get("family"),
        is_admin=admin_access
    )

    mission = next((m for m in missions if m.get("mission_id") == mission_id), None)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found or you don't have access to this mission"
        )

    return mission

class CompleteMissionRequest(BaseModel):
    mission_id: int
    player_id: Optional[int] = None
    completion_proof: Optional[str] = None  # For admin verification

@router.post("/complete")
async def complete_mission(
    request: CompleteMissionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    player = get_player_from_token(credentials)
    """
    Mark a mission as completed and update player stats
    Admin can complete missions for any player
    Players can only complete their own missions
    """
    current_player_id = player.get("player_id")
    target_player_id = request.player_id if request.player_id else current_player_id
    admin_access = is_admin(player.get("email"))

    # Non-admin users can only complete their own missions
    if not admin_access and current_player_id != target_player_id:
        raise HTTPException(
            status_code=403,
            detail="You can only complete your own missions"
        )

    # Get mission
    all_missions = get_all_missions()
    mission = next(
        (m for m in all_missions if m.get("mission_id") == request.mission_id),
        None
    )

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Check if already completed
    if mission.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Mission already completed")

    # Get target player
    target_player = get_player_by_id(target_player_id)
    if not target_player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Update mission status
    update_mission(request.mission_id, {
        "status": "completed",
        "completed_by": target_player_id,
        "completion_time": "now"  # In production, use actual timestamp
    })

    # Update player stats
    new_balance = float(target_player.get("balance", 0)) + float(mission.get("reward_md", 0))
    new_missions_completed = int(target_player.get("missions_completed", 0)) + 1

    updates = {
        "balance": new_balance,
        "missions_completed": new_missions_completed
    }

    # Add reward item if any
    reward_item = mission.get("reward_item", "")
    if reward_item:
        import json
        current_items = json.loads(target_player.get("items", "[]"))
        current_items.append(reward_item)
        updates["items"] = json.dumps(current_items)

    update_player(target_player_id, updates)

    # Update scorecard
    update_score(target_player_id, {
        "missions_completed": new_missions_completed,
        "total_score": new_missions_completed * 1000  # Simple scoring for now
    })

    return {
        "success": True,
        "mission_id": request.mission_id,
        "mission_title": mission.get("title"),
        "reward_md": mission.get("reward_md"),
        "reward_item": reward_item,
        "new_balance": new_balance,
        "missions_completed": new_missions_completed,
        "message": f"Mission '{mission.get('title')}' completed! +{mission.get('reward_md')} MD"
    }

# ==================== ADMIN ENDPOINTS ====================

class CreateMissionRequest(BaseModel):
    title: str
    description: str
    reward_md: int
    reward_item: Optional[str] = ""
    visibility: str = "public"  # public, private, family
    assigned_family: str = "all"
    assigned_role: str = "all"
    assigned_to: Optional[int] = None
    day: int = 1
    type: str = "General"

@router.post("/create")
async def create_mission(
    request: CreateMissionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    player = get_player_from_token(credentials)
    """
    Create a new mission (Admin or Don only)
    """
    from utils.google_client import is_don, add_mission

    admin_access = is_admin(player.get("email"))
    don_access = is_don(player.get("email"))

    # Only admin or don can create missions
    if not admin_access and not don_access:
        raise HTTPException(
            status_code=403,
            detail="Only Godfather or Family Dons can create missions"
        )

    # If Don, restrict to family missions only
    if don_access and not admin_access:
        if request.visibility != "family" or request.assigned_family != player.get("family"):
            raise HTTPException(
                status_code=403,
                detail="Dons can only create missions for their own family"
            )

    # Get next mission ID
    all_missions = get_all_missions()
    next_id = max([m.get("mission_id", 0) for m in all_missions], default=0) + 1

    mission_data = {
        "mission_id": next_id,
        "title": request.title,
        "description": request.description,
        "reward_md": request.reward_md,
        "reward_item": request.reward_item,
        "visibility": request.visibility,
        "assigned_family": request.assigned_family,
        "assigned_role": request.assigned_role,
        "assigned_to": request.assigned_to or "",
        "status": "available",
        "day": request.day,
        "type": request.type,
        "completed_by": "",
        "completion_time": ""
    }

    result = add_mission(mission_data)

    if result.get("success"):
        return {
            "success": True,
            "mission_id": next_id,
            "message": "Mission created successfully",
            "mission": mission_data
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("message"))

@router.get("/admin/all-missions")
async def get_all_missions_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    player = get_player_from_token(credentials)
    """
    Get all missions (admin only)
    """
    if not is_admin(player.get("username")):
        raise HTTPException(status_code=403, detail="Admin access required")

    missions = get_all_missions()
    return {
        "missions": missions,
        "total": len(missions)
    }
