from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
import os

from utils.google_client import (
    get_player_by_id, update_player, add_news, get_news,
    get_all_players, get_all_missions, update_mission,
    populate_spreadsheet_with_dummy_data, add_player_to_sheet
)
from utils.scoring import recalculate_player_score
from utils.email_notification_service import godfather_email_service

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def verify_admin(authorization: Optional[str] = Header(None)) -> bool:
    """Verify that the request is from an admin"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if user is admin (admin-uuid, player_id 0, role "Godfather" or "admin")
        player_id = payload.get("player_id")
        role = payload.get("role", "")

        if player_id == "admin-uuid" or player_id == 0 or role in ["Godfather", "admin"]:
            return True

        raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class UpdateMoneyRequest(BaseModel):
    player_id: str  # Can be UUID string or numeric ID
    amount: float
    reason: Optional[str] = None

@router.post("/update-money")
async def update_money(request: UpdateMoneyRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to add or subtract money from a player
    """
    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    current_balance = float(player.get("balance", 0))
    new_balance = current_balance + request.amount

    if new_balance < 0:
        new_balance = 0

    # Update player
    player["balance"] = new_balance
    new_score = recalculate_player_score(player)

    update_player(request.player_id, {
        "balance": new_balance,
        "individual_score": new_score
    })

    return {
        "success": True,
        "player_id": request.player_id,
        "player_name": player.get("name"),
        "old_balance": current_balance,
        "new_balance": new_balance,
        "change": request.amount,
        "reason": request.reason,
        "new_score": new_score
    }

class UpdatePlayerStatsRequest(BaseModel):
    player_id: str  # Can be UUID string or numeric ID
    missions_completed: Optional[int] = None
    puzzles_solved: Optional[int] = None
    kills_made: Optional[int] = None
    influence_points: Optional[float] = None
    alive: Optional[bool] = None

@router.post("/update-stats")
async def update_player_stats(request: UpdatePlayerStatsRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to update player stats
    """
    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    updates = {}

    if request.missions_completed is not None:
        updates["missions_completed"] = request.missions_completed
        player["missions_completed"] = request.missions_completed

    if request.puzzles_solved is not None:
        updates["puzzles_solved"] = request.puzzles_solved
        player["puzzles_solved"] = request.puzzles_solved

    if request.kills_made is not None:
        updates["kills_made"] = request.kills_made
        player["kills_made"] = request.kills_made

    if request.influence_points is not None:
        updates["influence_points"] = request.influence_points
        player["influence_points"] = request.influence_points

    if request.alive is not None:
        updates["alive"] = request.alive
        player["alive"] = request.alive

    # Recalculate score
    new_score = recalculate_player_score(player)
    updates["individual_score"] = new_score

    update_player(request.player_id, updates)

    return {
        "success": True,
        "player_id": request.player_id,
        "updates": updates,
        "new_score": new_score
    }

class UpdateItemsRequest(BaseModel):
    player_id: str
    items: List[str]

@router.post("/update-items")
async def update_player_items(request: UpdateItemsRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to update player items
    """
    import json

    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Convert items list to JSON string
    items_json = json.dumps(request.items)

    # Update player items
    update_player(request.player_id, {
        "items": items_json
    })

    return {
        "success": True,
        "player_id": request.player_id,
        "player_name": player.get("name"),
        "items": request.items,
        "total_items": len(request.items)
    }

class PublishNewsRequest(BaseModel):
    title: str
    message: str

@router.post("/publish-news")
async def publish_news(request: PublishNewsRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to publish news/announcements
    """
    add_news(request.title, request.message)

    return {
        "success": True,
        "title": request.title,
        "message": "News published successfully"
    }

@router.get("/news")
async def get_all_news(is_admin: bool = Depends(verify_admin)):
    """
    Get all news (admin view with more details)
    """
    news = get_news()

    return {
        "news": news,
        "total": len(news)
    }

@router.get("/dashboard")
async def admin_dashboard(is_admin: bool = Depends(verify_admin)):
    """
    Get admin dashboard statistics
    """
    players = get_all_players()
    missions = get_all_missions()

    alive_players = [p for p in players if p.get("alive", True)]
    dead_players = [p for p in players if not p.get("alive", True)]

    total_money = sum(float(p.get("balance", 0)) for p in players)
    completed_missions = [m for m in missions if m.get("completed")]

    return {
        "total_players": len(players),
        "alive_players": len(alive_players),
        "dead_players": len(dead_players),
        "total_missions": len(missions),
        "completed_missions": len(completed_missions),
        "total_money_in_game": total_money
    }

class EliminatePlayerRequest(BaseModel):
    player_id: int
    reason: Optional[str] = None

@router.post("/eliminate-player")
async def eliminate_player(request: EliminatePlayerRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to eliminate a player from the game
    """
    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    update_player(request.player_id, {"alive": False})

    return {
        "success": True,
        "player_id": request.player_id,
        "player_name": player.get("name"),
        "message": f"{player.get('name')} has been eliminated",
        "reason": request.reason
    }

class RevivePlayerRequest(BaseModel):
    player_id: int

@router.post("/revive-player")
async def revive_player(request: RevivePlayerRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to revive an eliminated player
    """
    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    update_player(request.player_id, {"alive": True})

    return {
        "success": True,
        "player_id": request.player_id,
        "player_name": player.get("name"),
        "message": f"{player.get('name')} has been revived"
    }

@router.post("/populate-spreadsheet")
async def populate_spreadsheet(is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to populate the Google Spreadsheet with dummy data
    WARNING: This will clear existing data and add 10 dummy users
    """
    result = populate_spreadsheet_with_dummy_data()
    return result

class AddPlayerRequest(BaseModel):
    player_id: int
    name: str
    username: str
    password: str
    role: str = "Soldier"
    family: str
    balance: float = 0
    missions_completed: int = 0
    puzzles_solved: int = 0
    kills_made: int = 0
    alive: bool = True
    influence_points: float = 0
    individual_score: float = 0
    items: str = "[]"

@router.post("/add-player")
async def add_new_player(request: AddPlayerRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to add a new player to the spreadsheet
    """
    player_data = request.dict()
    result = add_player_to_sheet(player_data)
    return result

class AssignRoleRequest(BaseModel):
    player_id: str
    role: str
    family: Optional[str] = None  # Family is optional
    balance: int = 0

@router.post("/assign-role")
async def assign_role(request: AssignRoleRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to assign role and optionally family to a player
    Role is required, family is optional
    Balance is NOT automatically assigned - Godfather must manually add money via Admin Tools
    """
    from utils.google_client import update_player_by_email, get_player_by_id
    import json

    player = get_player_by_id(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Items will be determined by physical envelopes, so always start with empty items
    items = json.dumps([])

    # Update player with role and optional family
    # Balance is NOT set here - Godfather will manually add money via Admin Tools
    # Update both "role" and "assigned_role" columns to ensure consistency
    updates = {
        "role": request.role,  # Main role column
        "assigned_role": request.role,  # Backup role column for compatibility
        "family": request.family if request.family else "",  # Family is optional
        "items": items  # Always empty - items determined by physical envelopes
    }

    # Use email to update since player might not have logged in yet
    from utils.google_client import update_player_by_email
    success = update_player_by_email(player.get("email"), updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign role")

    family_text = f" of {request.family} family" if request.family else ""
    return {
        "success": True,
        "player_id": request.player_id,
        "player_name": player.get("name"),
        "role": request.role,
        "family": request.family or "",
        "message": f"Assigned {request.role}{family_text} to {player.get('name')}. Use Admin Tools to set their balance."
    }

class AddMissionRequest(BaseModel):
    title: str
    description: str
    reward_md: float
    type: str
    visibility: str = "public"
    assigned_family: str = "all"
    assigned_role: str = "all"
    day: int = 1
    status: str = "active"
    completed: bool = False

@router.post("/add-mission")
async def add_new_mission(request: AddMissionRequest, is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to add a new mission to the spreadsheet
    """
    from utils.google_client import add_mission, get_all_missions

    # Get next mission ID
    all_missions = get_all_missions()
    next_id = max([m.get("mission_id", 0) for m in all_missions], default=0) + 1

    mission_data = {
        "mission_id": next_id,
        "title": request.title,
        "description": request.description,
        "reward_md": request.reward_md,
        "reward_item": "",  # Can be added later
        "visibility": request.visibility,
        "assigned_family": request.assigned_family,
        "assigned_role": request.assigned_role,
        "assigned_to": "",
        "status": request.status,
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
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to create mission"))

@router.delete("/clear-missions")
async def clear_all_missions(is_admin: bool = Depends(verify_admin)):
    """
    Admin endpoint to clear all missions from the spreadsheet
    """
    from utils.google_client import clear_all_missions

    result = clear_all_missions()

    if result.get("success"):
        return {
            "success": True,
            "message": "All missions cleared successfully"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to clear missions"))

# Game day management - Godfather controls
game_state = {
    "current_day": 1,
    "mission_unlock_hour": 9  # 9 AM IST
}

@router.get("/game-state")
async def get_game_state(is_admin: bool = Depends(verify_admin)):
    """
    Get current game state (day, unlock time)
    """
    return game_state

@router.post("/set-game-day")
async def set_game_day(day: int, is_admin: bool = Depends(verify_admin)):
    """
    Set the current game day
    """
    game_state["current_day"] = day
    return {
        "success": True,
        "current_day": day,
        "message": f"Game day set to {day}"
    }

@router.post("/set-unlock-hour")
async def set_unlock_hour(hour: int, is_admin: bool = Depends(verify_admin)):
    """
    Set the mission unlock hour (0-23)
    """
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="Hour must be between 0 and 23")

    game_state["mission_unlock_hour"] = hour
    return {
        "success": True,
        "unlock_hour": hour,
        "message": f"Mission unlock hour set to {hour}:00"
    }

# Email reminder endpoints
class EmailReminderRequest(BaseModel):
    blackmarket_time: Optional[str] = None
    recipient_type: str = "test"  # "test" or "all"

class DayStartEmailRequest(BaseModel):
    recipient_type: str = "test"  # "test" or "all"

class MissionUnlockEmailRequest(BaseModel):
    recipient_type: str = "test"  # "test" or "all"

@router.post("/send-day-start-email")
async def send_day_start_email(request: DayStartEmailRequest, is_admin: bool = Depends(verify_admin)):
    """
    Send day start reminder email to test or all users based on recipient_type
    """
    try:
        # Determine recipient list based on recipient_type
        if request.recipient_type == "all":
            # Get all players and extract their email addresses
            all_players = get_all_players()
            player_emails = [player.get("email") for player in all_players if player.get("email")]

            if not player_emails:
                raise HTTPException(status_code=400, detail="No player emails found")
        else:
            # Test mode - send only to test email
            player_emails = ["varun.mahurkar@oloid.ai"]

        current_day = game_state.get("current_day", 1)
        result = godfather_email_service.send_day_start_reminder(player_emails, current_day)

        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message"),
                "sent_count": result.get("sent_count"),
                "preview_url": result.get("preview_url"),
                "recipient_type": request.recipient_type
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")

@router.post("/send-mission-unlock-email")
async def send_mission_unlock_email(request: MissionUnlockEmailRequest, is_admin: bool = Depends(verify_admin)):
    """
    Send mission unlock reminder email to test or all users based on recipient_type
    """
    try:
        # Determine recipient list based on recipient_type
        if request.recipient_type == "all":
            # Get all players and extract their email addresses
            all_players = get_all_players()
            player_emails = [player.get("email") for player in all_players if player.get("email")]

            if not player_emails:
                raise HTTPException(status_code=400, detail="No player emails found")
        else:
            # Test mode - send only to test email
            player_emails = ["varun.mahurkar@oloid.ai"]

        current_day = game_state.get("current_day", 1)
        unlock_hour = game_state.get("mission_unlock_hour", 9)

        result = godfather_email_service.send_mission_reminder(player_emails, current_day, unlock_hour)

        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message"),
                "sent_count": result.get("sent_count"),
                "preview_url": result.get("preview_url"),
                "recipient_type": request.recipient_type
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")

@router.post("/send-blackmarket-email")
async def send_blackmarket_email(request: EmailReminderRequest, is_admin: bool = Depends(verify_admin)):
    """
    Send black market reminder email to test or all users based on recipient_type (5 mins before opening)
    """
    try:
        # Determine recipient list based on recipient_type
        if request.recipient_type == "all":
            # Get all players and extract their email addresses
            all_players = get_all_players()
            player_emails = [player.get("email") for player in all_players if player.get("email")]

            if not player_emails:
                raise HTTPException(status_code=400, detail="No player emails found")
        else:
            # Test mode - send only to test email
            player_emails = ["varun.mahurkar@oloid.ai"]

        blackmarket_time = request.blackmarket_time or "Soon"

        # You can pass item count if available from black market data
        result = godfather_email_service.send_blackmarket_reminder(player_emails, blackmarket_time)

        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message"),
                "sent_count": result.get("sent_count"),
                "preview_url": result.get("preview_url"),
                "recipient_type": request.recipient_type
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")
