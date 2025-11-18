from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import jwt
import os

from utils.google_client import get_player_by_id, update_player, add_trade
from utils.scoring import recalculate_player_score

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def get_current_player_id(authorization: Optional[str] = Header(None)) -> int:
    """Extract player ID from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("player_id")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class TransferMoneyRequest(BaseModel):
    to_player_id: int
    amount: float
    message: Optional[str] = None

@router.post("/transfer-money")
async def transfer_money(request: TransferMoneyRequest, current_player_id: int = Depends(get_current_player_id)):
    """
    Transfer money from current player to another player
    """
    # Validate amount
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Get sender
    from_player = get_player_by_id(current_player_id)
    if not from_player:
        raise HTTPException(status_code=404, detail="Sender not found")

    # Check if sender is alive
    if not from_player.get("alive", True):
        raise HTTPException(status_code=403, detail="Dead players cannot make transfers")

    # Get recipient
    to_player = get_player_by_id(request.to_player_id)
    if not to_player:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Check if recipient is alive
    if not to_player.get("alive", True):
        raise HTTPException(status_code=400, detail="Cannot transfer to eliminated players")

    # Check sender has enough money
    sender_balance = float(from_player.get("balance", 0))
    if sender_balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Perform transfer
    new_sender_balance = sender_balance - request.amount
    new_recipient_balance = float(to_player.get("balance", 0)) + request.amount

    # Update sender
    from_player["balance"] = new_sender_balance
    sender_score = recalculate_player_score(from_player)
    update_player(current_player_id, {
        "balance": new_sender_balance,
        "individual_score": sender_score
    })

    # Update recipient
    to_player["balance"] = new_recipient_balance
    recipient_score = recalculate_player_score(to_player)
    update_player(request.to_player_id, {
        "balance": new_recipient_balance,
        "individual_score": recipient_score
    })

    # Record trade
    add_trade(current_player_id, request.to_player_id, request.amount, "money")

    return {
        "success": True,
        "from_player": from_player.get("name"),
        "to_player": to_player.get("name"),
        "amount": request.amount,
        "new_balance": new_sender_balance,
        "message": f"Successfully transferred ${request.amount} to {to_player.get('name')}"
    }

@router.get("/history")
async def get_trade_history(current_player_id: int = Depends(get_current_player_id)):
    """
    Get trade history for current player
    """
    from utils.google_client import get_sheet

    sheet = get_sheet("Trades")
    if sheet is None:
        return {
            "trades": [],
            "message": "Trade history not available"
        }

    try:
        trades = sheet.get_all_records()

        # Filter trades involving current player
        player_trades = [
            t for t in trades
            if t.get("from_player") == current_player_id or t.get("to_player") == current_player_id
        ]

        return {
            "trades": player_trades,
            "total": len(player_trades)
        }
    except Exception as e:
        return {
            "trades": [],
            "error": str(e)
        }

@router.get("/all")
async def get_all_trades(current_player_id: int = Depends(get_current_player_id)):
    """
    Get all trades (public ledger)
    """
    from utils.google_client import get_sheet

    sheet = get_sheet("Trades")
    if sheet is None:
        return {
            "trades": [],
            "message": "Trade history not available"
        }

    try:
        trades = sheet.get_all_records()

        return {
            "trades": trades,
            "total": len(trades)
        }
    except Exception as e:
        return {
            "trades": [],
            "error": str(e)
        }
