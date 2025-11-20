from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/env-check")
async def check_environment():
    """Debug endpoint to check environment variables (remove in production)"""
    return {
        "SECRET_KEY_set": bool(os.getenv("SECRET_KEY")),
        "SPREADSHEET_URL_set": bool(os.getenv("SPREADSHEET_URL")),
        "GOOGLE_CREDENTIALS_set": bool(os.getenv("GOOGLE_CREDENTIALS")),
        "ADMIN_USERNAME_set": bool(os.getenv("ADMIN_USERNAME")),
        "FRONTEND_URL_set": bool(os.getenv("FRONTEND_URL")),
        "SMTP_EMAIL_set": bool(os.getenv("SMTP_EMAIL")),
        "SECRET_KEY_length": len(os.getenv("SECRET_KEY", "")),
        "GOOGLE_CREDENTIALS_length": len(os.getenv("GOOGLE_CREDENTIALS", ""))
    }

@router.get("/sheets-test")
async def test_sheets_connection():
    """Test Google Sheets connection"""
    from utils.google_client import get_all_players, get_all_missions

    try:
        players = get_all_players()
        missions = get_all_missions()

        return {
            "success": True,
            "players_count": len(players),
            "missions_count": len(missions),
            "sample_player": players[0] if players else None,
            "sample_mission": missions[0] if missions else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
