import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional, List, Dict
import os
import json

# Global sheet client
sheet_client: Optional[gspread.Client] = None
spreadsheet = None

def init_sheets():
    """Initialize Google Sheets connection"""
    global sheet_client, spreadsheet

    try:
        # Define the scope
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        # Try to get credentials from environment variable first (for Vercel deployment)
        google_creds_json = os.getenv("GOOGLE_CREDENTIALS")

        if google_creds_json:
            # Use credentials from environment variable
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            sheet_client = gspread.authorize(creds)
        else:
            # Fall back to credentials file (for local development)
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "cred.json")

            if not os.path.exists(creds_path):
                print(f"Warning: Credentials file not found at {creds_path}")
                print("Using mock data mode. Create cred.json to connect to Google Sheets.")
                return None

            # Authenticate
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            sheet_client = gspread.authorize(creds)

        # Open the spreadsheet
        sheet_url = os.getenv("SPREADSHEET_URL", "")
        if sheet_url:
            spreadsheet = sheet_client.open_by_url(sheet_url)
        else:
            spreadsheet = sheet_client.open("Godfather Office Mafia")

        print("SUCCESS: Google Sheets connected successfully!")
        return spreadsheet

    except Exception as e:
        print(f"ERROR: Error connecting to Google Sheets: {e}")
        print("Running in mock data mode.")
        return None

def get_sheet(sheet_name: str):
    """Get a specific sheet by name"""
    if spreadsheet is None:
        return None
    try:
        return spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print(f"Error accessing sheet '{sheet_name}': {e}")
        return None

# ==================== PLAYERS SHEET ====================

def get_all_players():
    """Get all players from the players sheet"""
    sheet = get_sheet("players")
    if sheet is None:
        return get_mock_players()

    try:
        records = sheet.get_all_records()
        # Return all players - even those without UUID (for login to work)
        # Filter out completely empty rows (no email)
        players = [r for r in records if r.get("email")]
        return players
    except Exception as e:
        print(f"Error fetching players: {e}")
        return get_mock_players()

def get_player_by_email(email: str):
    """Get a player by email"""
    players = get_all_players()
    for player in players:
        if player.get("email") == email:
            return player
    return None

def get_player_by_username(username: str):
    """Get a player by username (deprecated - use get_player_by_email)"""
    return get_player_by_email(username)

def get_player_by_id(player_id: str):
    """Get a player by UUID"""
    players = get_all_players()
    for player in players:
        if player.get("player_id") == player_id:
            return player
    return None

def get_players_by_family(family_name: str):
    """Get all players from a specific family"""
    players = get_all_players()
    return [p for p in players if p.get("family") == family_name]

def update_player(player_id: str, updates: dict):
    """Update a player's data in the players sheet by UUID"""
    sheet = get_sheet("players")
    if sheet is None:
        print(f"Mock update for player {player_id}: {updates}")
        return True

    try:
        # If player_id is empty, find by email
        if not player_id and "email" in updates:
            all_data = sheet.get_all_values()
            headers = all_data[0]
            email_col = headers.index("email") + 1 if "email" in headers else None

            if email_col:
                cells = sheet.findall(updates["email"], in_column=email_col)
                if cells:
                    cell = cells[0]
                else:
                    return False
            else:
                return False
        else:
            # Find the row with the player_id (UUID)
            cell = sheet.find(str(player_id))

        if cell:
            row_num = cell.row
            headers = sheet.row_values(1)

            for key, value in updates.items():
                if key in headers:
                    col_num = headers.index(key) + 1
                    sheet.update_cell(row_num, col_num, value)

            return True
    except Exception as e:
        print(f"Error updating player: {e}")
        return False

def update_player_by_email(email: str, updates: dict):
    """Update a player's data by email"""
    sheet = get_sheet("players")
    if sheet is None:
        print(f"Mock update for player {email}: {updates}")
        return True

    try:
        print(f"[OK] Attempting to update player with email: {email}")
        print(f"[OK] Updates to apply: {updates}")

        all_data = sheet.get_all_values()
        headers = all_data[0]
        print(f"[OK] Found headers: {headers}")

        email_col = headers.index("email") + 1 if "email" in headers else None

        if not email_col:
            print(f"[ERROR] Email column not found in headers")
            return False

        cells = sheet.findall(email, in_column=email_col)
        if cells:
            row_num = cells[0].row
            print(f"[OK] Found player at row {row_num}")

            for key, value in updates.items():
                if key in headers:
                    col_num = headers.index(key) + 1
                    print(f"[OK] Updating {key} (col {col_num}) to: {value}")
                    sheet.update_cell(row_num, col_num, value)
                else:
                    print(f"[WARNING] Column '{key}' not found in headers")

            print(f"[OK] Successfully updated player {email}")
            return True
        else:
            print(f"[ERROR] Player with email {email} not found in sheet")
            return False
    except Exception as e:
        print(f"[ERROR] Exception updating player by email: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== MISSIONS SHEET ====================

def get_all_missions():
    """Get all missions from the missions sheet"""
    sheet = get_sheet("missions")
    if sheet is None:
        return get_mock_missions()

    try:
        records = sheet.get_all_records()
        missions = [r for r in records if r.get("mission_id")]
        return missions
    except Exception as e:
        print(f"Error fetching missions: {e}")
        return get_mock_missions()

def get_missions_for_player(player_id: int, role: str, family: str, is_admin: bool = False):
    """Get missions visible to a specific player based on their role and family"""
    missions = get_all_missions()

    # Admin sees everything
    if is_admin:
        return missions

    visible_missions = []
    for mission in missions:
        visibility = mission.get("visibility", "public")
        assigned_family = mission.get("assigned_family", "all")
        assigned_role = mission.get("assigned_role", "all")

        # Public missions visible to all
        if visibility == "public":
            # Check if mission is for specific family or role
            if (assigned_family == "all" or assigned_family == family) and \
               (assigned_role == "all" or assigned_role == role):
                visible_missions.append(mission)

        # Private missions only for assigned player
        elif visibility == "private":
            if mission.get("assigned_to") == player_id:
                visible_missions.append(mission)

        # Family missions only for family members
        elif visibility == "family":
            if assigned_family == family:
                visible_missions.append(mission)

    return visible_missions

def update_mission(mission_id: int, updates: dict):
    """Update mission status in the missions sheet"""
    sheet = get_sheet("missions")
    if sheet is None:
        print(f"Mock update for mission {mission_id}: {updates}")
        return True

    try:
        cell = sheet.find(str(mission_id))
        if cell:
            row_num = cell.row
            headers = sheet.row_values(1)

            for key, value in updates.items():
                if key in headers:
                    col_num = headers.index(key) + 1
                    sheet.update_cell(row_num, col_num, value)

            return True
    except Exception as e:
        print(f"Error updating mission: {e}")
        return False

def add_mission(mission_data: dict):
    """Add a new mission to the missions sheet"""
    sheet = get_sheet("missions")
    if sheet is None:
        return {"success": False, "message": "Could not connect to Google Sheets"}

    try:
        headers = sheet.row_values(1)
        row = [mission_data.get(h, "") for h in headers]
        sheet.append_row(row)
        return {"success": True, "message": "Mission added successfully"}
    except Exception as e:
        print(f"Error adding mission: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

def clear_all_missions():
    """Clear all missions from the missions sheet (keep headers)"""
    sheet = get_sheet("missions")
    if sheet is None:
        return {"success": False, "message": "Could not connect to Google Sheets"}

    try:
        # Get headers
        headers = sheet.row_values(1)
        # Clear all data
        sheet.clear()
        # Restore headers
        sheet.append_row(headers)
        return {"success": True, "message": "All missions cleared successfully"}
    except Exception as e:
        print(f"Error clearing missions: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

# ==================== SCORECARD SHEET ====================

def get_all_scores():
    """Get all scores from the scorecard sheet"""
    sheet = get_sheet("scoreboard")
    if sheet is None:
        return get_mock_scores()

    try:
        records = sheet.get_all_records()
        return records
    except Exception as e:
        print(f"Error fetching scores: {e}")
        return get_mock_scores()

def update_score(player_id: int, score_updates: dict):
    """Update a player's score in the scorecard sheet"""
    sheet = get_sheet("scoreboard")
    if sheet is None:
        print(f"Mock score update for player {player_id}: {score_updates}")
        return True

    try:
        cell = sheet.find(str(player_id))
        if cell:
            row_num = cell.row
            headers = sheet.row_values(1)

            for key, value in score_updates.items():
                if key in headers:
                    col_num = headers.index(key) + 1
                    sheet.update_cell(row_num, col_num, value)

            return True
    except Exception as e:
        print(f"Error updating score: {e}")
        return False

# ==================== FAMILIES & AGGREGATION ====================

def get_families():
    """Get all families aggregated from players sheet"""
    players = get_all_players()
    families_dict = {}

    for player in players:
        if not player.get("family"):
            continue

        family_name = player.get("family")
        if family_name not in families_dict:
            families_dict[family_name] = {
                "family_name": family_name,
                "don": "",
                "total_money": 0,
                "members": 0,
                "kills": 0,
                "missions_completed": 0
            }

        families_dict[family_name]["total_money"] += player.get("balance", 0)
        families_dict[family_name]["members"] += 1
        families_dict[family_name]["kills"] += player.get("kills_made", 0)
        families_dict[family_name]["missions_completed"] += player.get("missions_completed", 0)

        # Set the don
        if player.get("role", "").lower() == "don":
            families_dict[family_name]["don"] = player.get("name", "")

    return list(families_dict.values())

def get_leaderboard(limit: int = 20):
    """Get top players from scorecard"""
    scores = get_all_scores()
    # Sort by total_score descending
    sorted_scores = sorted(scores, key=lambda x: x.get("total_score", 0), reverse=True)
    return sorted_scores[:limit]

# ==================== TRADES & TRANSACTIONS ====================

def add_trade(from_player: int, to_player: int, amount: float, item: str = "MD", trade_type: str = "public"):
    """Record a trade between players"""
    # Update sender's balance
    sender = get_player_by_id(from_player)
    if sender:
        new_balance = sender.get("balance", 0) - amount
        update_player(from_player, {"balance": new_balance})

    # Update receiver's balance
    receiver = get_player_by_id(to_player)
    if receiver:
        new_balance = receiver.get("balance", 0) + amount
        update_player(to_player, {"balance": new_balance})

        # Update trades_completed
        trades_completed = receiver.get("trades_completed", 0) + 1
        update_player(to_player, {"trades_completed": trades_completed})

    return True

# ==================== NEWS & ANNOUNCEMENTS ====================

news_storage = []

def get_news():
    """Get all news/announcements"""
    return news_storage

def add_news(title: str, message: str):
    """Add a news announcement"""
    news_item = {
        "id": len(news_storage) + 1,
        "title": title,
        "message": message
    }
    news_storage.append(news_item)
    print(f"News added: {title} - {message}")
    return True

# ==================== ADMIN FUNCTIONS ====================

def is_admin(email: str) -> bool:
    """Check if user is admin (Godfather)"""
    import os
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai")

    # Check if email matches admin email
    if email == ADMIN_USERNAME or email == "godfather":
        return True

    player = get_player_by_email(email)
    if player:
        role = player.get("role", "") or player.get("assigned_role", "")
        return role.lower() == "godfather"
    return False

def is_don(email: str) -> bool:
    """Check if user is a family Don"""
    player = get_player_by_email(email)
    if player:
        role = player.get("role", "") or player.get("assigned_role", "")
        return role.lower() == "don"
    return False

# ==================== MOCK DATA ====================

def get_mock_players():
    """Return mock player data"""
    return [
        {
            "player_id": 1,
            "name": "Don Corleone",
            "username": "godfather",
            "role": "Godfather",
            "family": "Corleone",
            "balance": 500000,
            "missions_completed": 0,
            "kills_made": 0,
            "alive": True,
            "items": json.dumps(["Vault Key", "Family Ring"]),
            "password": "godfather123"
        }
    ]

def get_mock_missions(day=None, player_id=None):
    """Return mock mission data"""
    return [
        {
            "mission_id": 1,
            "title": "Collect Protection Money",
            "description": "Visit 5 departments and collect protection fees",
            "reward_md": 15000,
            "reward_item": "",
            "visibility": "public",
            "assigned_family": "all",
            "assigned_role": "all",
            "assigned_to": "",
            "status": "available",
            "day": 1
        }
    ]

def get_mock_scores():
    """Return mock score data"""
    return [
        {
            "player_id": 1,
            "name": "Don Corleone",
            "role": "Godfather",
            "family": "Corleone",
            "missions_completed": 0,
            "bonus_points": 0,
            "total_score": 0
        }
    ]

def populate_spreadsheet_with_dummy_data():
    """Populate the spreadsheet with dummy data (admin feature)"""
    sheet = get_sheet("players")
    if sheet is None:
        return {"success": False, "message": "Could not connect to Google Sheets"}

    try:
        # This would clear and populate the sheet with dummy data
        # For now, return a simple success message
        return {
            "success": True,
            "message": "Spreadsheet population not implemented. Use populate_sheets.py script instead."
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def add_player_to_sheet(player_data: dict):
    """Add a new player to the players sheet"""
    sheet = get_sheet("players")
    if sheet is None:
        return {"success": False, "message": "Could not connect to Google Sheets"}

    try:
        headers = sheet.row_values(1)
        row = [player_data.get(h, "") for h in headers]
        sheet.append_row(row)
        return {
            "success": True,
            "message": "Player added successfully",
            "player": player_data
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
