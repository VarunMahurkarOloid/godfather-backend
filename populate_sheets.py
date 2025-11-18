"""
Populate all 3 Google Sheets with data
- players: All players + headers (basic info only)
- missions: Missions + headers
- scorecard: Score tracking + headers

INSTRUCTIONS:
1. Fill in PLAYER_EMAILS array with all real email addresses
2. Fill in PLAYER_PASSWORDS array with all passwords (same order as emails)
3. PLAYER_NAMES is already filled with names
4. Run: python populate_sheets.py
5. Players will be added with basic info only (name, email, password)
6. Admin will assign families, roles, and balances later through the admin panel
   - Families can be: Tattaglia, Barzini, Cuneo, Stracci (or any custom families)
   - Roles can be: Don, Caporegime, Detective, Merchant, Doctor, Citizen
"""

import json
import random
import uuid
from dotenv import load_dotenv
from utils.google_client import init_sheets, get_sheet

# Load environment variables
load_dotenv()

# ==================== REAL PLAYER DATA ====================
# Player Names - Godfather first, then all players
PLAYER_NAMES = [
    "Varun Mahurkar",  # Godfather
    "Adarsha Meher",
    "Akash Kakkar",
    "Aman Bhargava",
    "Amit Pathak",
    "Anilkumar Koda",
    "Anshul Bansal",
    "Arnav Gupta",
    "Ashish Tayal",
    "Bandi Vikas Reddy",
    "Barath B",
    "Brijeshkumar Mahendrabhai Patel",
    "Chandan Balesh Jain",
    "Chandra Prakash Mangipudi",
    "Harshit Kumar",
    "Hemaroop Inupakutika",
    "Hitesh Singhal",
    "Jasir V V",
    "Jay Nandan Sharma",
    "Karan Verma",
    "Kavitha Kamath",
    "Krishna G",
    "Lavanya Gupta",
    "Madhu M",
    "Mahek Parmar",
    "Manish",
    "Manmeet Mehta",
    "Megha Agarawal",
    "Mohit Sati",
    "Nishant",
    "Pooja Joshi",
    "Prabhat Ranjan",
    "Prajwal H S",
    "Rahul Mathew",
    "Rangaiah L R",
    "Sahana Ts",
    "Sampurna Kumar Dash",
    "Shankar Agarwal",
    "Shreya Basavanahalli Anil",
    "Shubham Kuntal",
    "Sinduja Rajagandhi",
    "Sneha",
    "Somshekhar",
    "Sumit Acharya",
    "Tanvi Mittal",
    "Tirupati Nigam",
    "Varsha Basutkar",
    "Veerabhadra Sajjan",
    "Vignesh B",
    "Vishal Sharma",
    "Hemalatha Gowda",
    "Sangeeta",
    "Subramani",
    "Yashu Agarwal",
    "Sashanth S",
    "Jagad Sankar",
    "Roshan Kumar",
    "KK"
]


# Player Emails - Godfather first, then all players
PLAYER_EMAILS = [
    "varun.mahurkar@oloid.ai",  # Godfather
    "adarsha.meher@oloid.ai",
    "akash.kakkar@oloid.ai",
    "aman.bhargava@oloid.ai",
    "amit.pathak@oloid.ai",
    "anil.kumar@oloid.ai",
    "anshul.bansal@oloid.ai",
    "arnav@oloid.ai",
    "ashish.tayal@oloid.ai",
    "vikas.bandi@oloid.ai",
    "barath.b@oloid.ai",
    "brijesh@oloid.ai",
    "chandan.jain@oloid.ai",
    "chandra@oloid.ai",
    "harshit.kumar@oloid.ai",
    "hemaroop@oloid.ai",
    "hitesh.singhal@oloid.ai",
    "jasir@oloid.ai",
    "jay.sharma@oloid.ai",
    "karan.verma@oloid.ai",
    "kavitha.kamath@oloid.ai",
    "krishna.gangavathikar@oloid.ai",
    "lavanya.gupta@oloid.ai",
    "madhu@oloid.ai",
    "design@oloid.ai",
    "manish.poojary@oloid.ai",
    "manmeet.mehta@oloid.ai",
    "megha@oloid.ai",
    "mohit.sati@oloid.ai",
    "nishant.rajpoot@xcdify.com",
    "pooja@oloid.ai",
    "prabhat@oloid.ai",
    "prajwal@oloid.ai",
    "rahul.mathew@oloid.ai",
    "rangaiah.lr@oloid.ai",
    "sahana.ts@oloid.ai",
    "sampurna@oloid.ai",
    "shankar@oloid.ai",
    "shreya.ba@oloid.ai",
    "shubham.kuntal@oloid.ai",
    "sinduja.rajagandhi@oloid.ai",
    "sneha.vastrad@oloid.ai",
    "somshekhar.bhimalli@oloid.ai",
    "sumit@oloid.ai",
    "tanvi@oloid.ai",
    "tirupati.nigam@oloid.ai",
    "varsha.basutkar@oloid.ai",
    "veerabhadra.sajjan@oloid.ai",
    "vignesh.b@oloid.ai",
    "vishal.sharma@oloid.ai",
    "hemalatha.gowda@oloid.ai",
    "sangeeta.sajjan@oloid.ai",
    "subramani.karalam@oloid.ai",
    "yashu.agrawal@oloid.ai",
    "sashanth.s@oloid.ai",
    "jagad.sankar@oloid.ai",
    "roshan.kumar@oloid.ai",
    "kk.karuppaiah@oloid.ai"
]


# Player Passwords - Godfather first, then all players
PLAYER_PASSWORDS = [
    "godfatheradmin@12345varun",  # varun.mahurkar@oloid.ai (Godfather)
    "nXlPB8",  # adarsha.meher@oloid.ai
    "qH4CVh",  # akash.kakkar@oloid.ai
    "zbKSlA",  # aman.bhargava@oloid.ai
    "1XYyIQ",  # amit.pathak@oloid.ai
    "pB6PAV",  # anil.kumar@oloid.ai
    "HM91QE",  # anshul.bansal@oloid.ai
    "H5BC0f",  # arnav@oloid.ai
    "SXb5pK",  # ashish.tayal@oloid.ai
    "QwyQNT",  # vikas.bandi@oloid.ai
    "q2XSKS",  # barath.b@oloid.ai
    "t8gP2z",  # brijesh@oloid.ai
    "Z4mRe9",  # chandan.jain@oloid.ai
    "aK7sV0",  # chandra@oloid.ai
    "Gv2cLQ",  # harshit.kumar@oloid.ai
    "9hR3yB",  # hemaroop@oloid.ai
    "fP6WqN",  # hitesh.singhal@oloid.ai
    "Rc2D8u",  # jasir@oloid.ai
    "Jp8sM4",  # jay.sharma@oloid.ai
    "k9VbY1",  # karan.verma@oloid.ai
    "MZ3qH7",  # kavitha.kamath@oloid.ai
    "y2TnR5",  # krishna.gangavathikar@oloid.ai
    "B7uF0x",  # lavanya.gupta@oloid.ai
    "c4QeA6",  # madhu@oloid.ai
    "dW9kS3",  # design@oloid.ai
    "Lr6Pz8",  # manish.poojary@oloid.ai
    "V5nHy2",  # manmeet.mehta@oloid.ai
    "s3XJq7",  # megha@oloid.ai
    "N8mC4v",  # mohit.sati@oloid.ai
    "u2RkZ9",  # nishant.rajpoot@xcdify.com
    "F6yPb1",  # pooja@oloid.ai
    "eW7qT4",  # prabhat@oloid.ai
    "H2zMv8",  # prajwal@oloid.ai
    "p9QfG3",  # rahul.mathew@oloid.ai
    "S4tN0k",  # rangaiah.lr@oloid.ai
    "g1LxY7",  # sahana.ts@oloid.ai
    "R6aVw2",  # sampurna@oloid.ai
    "z3KpM9",  # shankar@oloid.ai
    "Y7cQe5",  # shreya.ba@oloid.ai
    "m5HnB2",  # shubham.kuntal@oloid.ai
    "T9vR4p",  # sinduja.rajagandhi@oloid.ai
    "q6XjC8",  # sneha.vastrad@oloid.ai
    "W2sF9y",  # somshekhar.bhimalli@oloid.ai
    "K8uD3r",  # sumit@oloid.ai
    "c7ZpL1",  # tanvi@oloid.ai
    "A4mR6v",  # tirupati.nigam@oloid.ai
    "h3TqY8",  # varsha.basutkar@oloid.ai
    "b9SxK2",  # veerabhadra.sajjan@oloid.ai
    "U6dJ7z",  # vignesh.b@oloid.ai
    "o2RkH5",  # vishal.sharma@oloid.ai
    "X8qB4t",  # hemalatha.gowda@oloid.ai
    "n3FvP9",  # sangeeta.sajjan@oloid.ai
    "L5yW2c",  # subramani.karalam@oloid.ai
    "P7hM0x",  # yashu.agrawal@oloid.ai
    "r4KzV6",  # sashanth.s@oloid.ai
    "Y1qN8b",  # jagad.sankar@oloid.ai
    "s8Tg3p",  # roshan.kumar@oloid.ai
    "k6WvR2"   # kk@oloid.ai
]

def get_player_data(index):
    """Get player data by index from the arrays"""
    return {
        "name": PLAYER_NAMES[index],
        "email": PLAYER_EMAILS[index],
        "password": PLAYER_PASSWORDS[index]
    }

def populate_players_sheet():
    """Populate players sheet with all players (basic info only)"""
    sheet = get_sheet("players")
    if not sheet:
        return False

    sheet.clear()

    headers = [
        "player_id", "name", "email", "password", "role", "family",
        "balance", "items", "status", "alive", "missions_completed",
        "kills_made", "heals_performed", "trades_completed",
        "vault_contribution", "bonus_points", "total_score",
        "registered", "phone_number", "assigned_role", "notes"
    ]

    data = [headers]

    for player_index in range(len(PLAYER_NAMES)):
        player = get_player_data(player_index)
        player_uuid = str(uuid.uuid4())  # Generate UUID for every player

        if player_index == 0:
            # Godfather - pre-assigned with role and unlimited balance
            data.append([
                player_uuid, player["name"], player["email"], player["password"],
                "Godfather", "", 999999999,
                json.dumps(["Master Key", "Admin Badge"]),
                "Active", "TRUE", 0, 0, 0, 0, 0, 0, 0, "TRUE", "", "Godfather", "Game Administrator"
            ])
        else:
            # Regular players - UUID assigned, waiting for role assignment
            data.append([
                player_uuid, player["name"], player["email"], player["password"],
                "", "", 0, json.dumps([]),
                "Active", "TRUE", 0, 0, 0, 0, 0, 0, 0, "FALSE", "", "", ""
            ])

    sheet.update('A1', data)
    print(f"[OK] Players: {len(data)-1} added with UUIDs (1 Godfather + {len(data)-2} pending assignment)")
    return True

def populate_missions_sheet():
    """Populate missions sheet"""
    sheet = get_sheet("missions")
    if not sheet:
        return False

    sheet.clear()

    headers = [
        "mission_id", "title", "description", "reward_md", "reward_item",
        "visibility", "assigned_family", "assigned_role", "assigned_to",
        "status", "day", "type", "completed_by", "completion_time"
    ]

    missions_data = [
        [1, "Territory Expansion", "Take a photo with 5 members from different families", 15000, "", "public", "all", "all", "", "available", 1, "Physical", "", ""],
        [2, "Code Breaker", "Solve the cipher: UJQQFS = ?", 10000, "Secret Letter", "public", "all", "all", "", "available", 1, "Mental", "", ""],
        [3, "Protection Racket", "Visit the cafeteria and collect 3 signatures", 12000, "", "public", "all", "all", "", "available", 1, "Physical", "", ""],
        [4, "Information Network", "Find out the birthday of a player from each family", 8000, "", "public", "all", "Detective", "", "available", 1, "Investigation", "", ""],
        [5, "Black Market Deal", "Trade items worth 50,000 MD total", 20000, "Vault Key", "public", "all", "Merchant", "", "available", 2, "Trade", "", ""],
        [6, "Street Contacts", "Collect information from 3 different departments", 10000, "", "public", "all", "all", "", "available", 1, "Investigation", "", ""],
        [7, "Muscle Work", "Complete 3 physical challenges", 15000, "", "public", "all", "Caporegime", "", "available", 2, "Physical", "", ""],
        [8, "Family Business", "Collect 100,000 MD for family vault", 25000, "Family Ring", "family", "Tattaglia", "all", "", "available", 1, "Economic", "", ""],
        [9, "Family Honor", "Win 3 missions as a family", 30000, "", "family", "Barzini", "all", "", "available", 1, "Competition", "", ""],
        [10, "Territory Control", "Control 3 key locations", 35000, "Safe Pass", "family", "Cuneo", "all", "", "available", 2, "Strategic", "", ""],
        [11, "Family Alliance", "Form alliance with another family", 20000, "", "family", "Stracci", "Don", "", "available", 2, "Diplomacy", "", ""],
        [12, "Medical Emergency", "Successfully heal 3 players", 15000, "Medical Kit", "public", "all", "Doctor", "", "available", 1, "Support", "", ""],
        [13, "Capo Leadership", "Lead crew to complete 5 missions", 25000, "", "public", "all", "Caporegime", "", "available", 2, "Leadership", "", ""],
        [14, "Intelligence Report", "Submit report on rival family", 18000, "Bribe Note", "public", "all", "Detective", "", "available", 2, "Investigation", "", ""],
        [15, "Final Showdown", "Be in top 3 of your family", 50000, "Secret Letter", "public", "all", "all", "", "available", 3, "Competition", "", ""],
        [16, "Loyalty Test", "Donate 50,000 MD to family vault", 75000, "", "public", "all", "all", "", "available", 3, "Economic", "", ""],
        [17, "Last Stand", "Survive until end of day 3", 40000, "Safe Pass", "public", "all", "all", "", "available", 3, "Survival", "", ""],
        [18, "Grand Heist", "Complete the main objective", 100000, "Golden Ring", "public", "all", "all", "", "available", 3, "Special", "", ""],
    ]

    data = [headers] + missions_data
    sheet.update('A1', data)
    print(f"[OK] Missions: {len(missions_data)} added")
    return True

def populate_scorecard_sheet():
    """Populate scorecard sheet"""
    sheet = get_sheet("scoreboard")
    if not sheet:
        return False

    sheet.clear()

    headers = [
        "player_id", "name", "email", "role", "family", "missions_completed",
        "bonus_points", "vault_contribution", "kills_made",
        "trades_completed", "total_score", "rank"
    ]

    players_sheet = get_sheet("players")
    if players_sheet:
        players_data = players_sheet.get_all_values()[1:]
        data = [headers]
        for player in players_data:
            if player and len(player) >= 6:
                data.append([
                    player[0], player[1], player[2], player[4], player[5],
                    0, 0, 0, 0, 0, 0, ""
                ])

        sheet.update('A1', data)
        print(f"[OK] Scorecard: {len(data)-1} entries initialized")
        return True
    else:
        return False

def main():
    print("\n" + "="*60)
    print("GODFATHER - GOOGLE SHEETS POPULATION")
    print("="*60)

    spreadsheet = init_sheets()
    if not spreadsheet:
        print("\n[ERROR] Could not connect to Google Sheets")
        print("  Check: cred.json, SPREADSHEET_URL in .env, API enabled")
        return

    print(f"[OK] Connected: {spreadsheet.title}\n")

    success = populate_players_sheet() and populate_missions_sheet() and populate_scorecard_sheet()

    if success:
        print(f"\n{'='*60}")
        print("SETUP COMPLETE - Game Ready!")
        print(f"{'='*60}")
        print(f"\nGodfather Login: {PLAYER_EMAILS[0]} | {PLAYER_PASSWORDS[0]}")
        print(f"Total Players: {len(PLAYER_NAMES)} (all with UUIDs, 1 Godfather + {len(PLAYER_NAMES)-1} awaiting assignment)")
        print("\nRestart backend server to load data.")
    else:
        print("\n[ERROR] Population failed")

if __name__ == "__main__":
    main()
