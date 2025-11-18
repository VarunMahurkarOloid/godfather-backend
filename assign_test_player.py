"""
Quick script to assign one test player a family and role for testing
"""
import json
from dotenv import load_dotenv
from utils.google_client import init_sheets, get_sheet, update_player_by_email

load_dotenv()

# Initialize connection
spreadsheet = init_sheets()
if not spreadsheet:
    print("ERROR: Could not connect to Google Sheets!")
    exit(1)

print("Connected to Google Sheets")

# Assign first player (Adarsha Meher) a family and role
test_email = "adarsha.meher@oloid.ai"

updates = {
    "family": "Tattaglia",
    "assigned_role": "Don",
    "balance": 250000,
    "items": json.dumps(["Vault Key", "Family Ring"]),
    "notes": "Test player - Don of Tattaglia family"
}

print(f"Assigning {test_email} as Don of Tattaglia family...")
success = update_player_by_email(test_email, updates)

if success:
    print(f"SUCCESS: Assigned role to {test_email}")
    print(f"  Family: Tattaglia")
    print(f"  Role: Don")
    print(f"  Balance: $250,000")
    print(f"\nYou can now login with:")
    print(f"  Email: {test_email}")
    print(f"  Password: nXlPB8")
    print(f"  Role: Don")
else:
    print("ERROR: Failed to assign role")
