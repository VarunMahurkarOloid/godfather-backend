from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
import os
import json
from datetime import datetime
import pytz

from utils.google_client import get_player_by_id, update_player, get_sheet, is_admin
from utils.scoring import recalculate_player_score

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def get_current_player(authorization: Optional[str] = Header(None)):
    """Extract player info from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        player_id = payload.get("player_id")

        # Handle admin special case
        if player_id == "admin-uuid":
            ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "varun.mahurkar@oloid.ai")
            return {
                "player_id": "admin-uuid",
                "name": "Varun Mahurkar (Godfather)",
                "email": ADMIN_USERNAME,
                "role": "Godfather",
                "family": "Administration",
                "balance": 999999999,
                "alive": True,
                "is_admin": True
            }

        # Get full player data
        player = get_player_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        return player
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def is_market_open():
    """Check if black market is open (11:11 PM IST)"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    hour = current_time.hour
    minute = current_time.minute

    # Market is open from 11:11 PM to midnight (23:11 to 23:59)
    # and from midnight to 11 minutes past midnight (00:00 to 00:11)
    return (hour == 23 and minute >= 11) or (hour == 0 and minute < 11)

def get_blackmarket_sheet():
    """Get the market sheet"""
    return get_sheet("market")

@router.get("/offers")
async def get_offers(player: dict = Depends(get_current_player)):
    """
    Get all black market offers
    Players can see offers anytime, but can only purchase when market is open
    """
    sheet = get_blackmarket_sheet()
    if sheet is None:
        return {
            "offers": [],
            "market_open": is_market_open(),
            "message": "Black Market not available"
        }

    try:
        offers = sheet.get_all_records()

        # Format offers with availability status
        formatted_offers = []
        for offer in offers:
            formatted_offers.append({
                "offer_id": offer.get("offer_id"),
                "item_name": offer.get("item_name"),
                "description": offer.get("description", ""),
                "price": float(offer.get("price", 0)),
                "quantity_available": int(offer.get("quantity_available", 0)),
                "available": int(offer.get("quantity_available", 0)) > 0
            })

        return {
            "offers": formatted_offers,
            "market_open": is_market_open(),
            "total": len(formatted_offers)
        }
    except Exception as e:
        return {
            "offers": [],
            "market_open": is_market_open(),
            "error": str(e)
        }

@router.post("/purchase/{offer_id}")
async def purchase_offer(offer_id: int, player: dict = Depends(get_current_player)):
    """
    Purchase an item from the black market
    Only works when market is open
    """
    # Check if market is open
    if not is_market_open():
        raise HTTPException(
            status_code=403,
            detail="Black Market is closed. Opens at 11:11 PM IST"
        )

    # Check if player is alive
    if not player.get("alive", True):
        raise HTTPException(status_code=403, detail="Dead players cannot make purchases")

    sheet = get_blackmarket_sheet()
    if sheet is None:
        raise HTTPException(status_code=500, detail="Black Market not available")

    try:
        offers = sheet.get_all_records()
        offer = next((o for o in offers if o.get("offer_id") == offer_id), None)

        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        # Check quantity
        quantity_available = int(offer.get("quantity_available", 0))
        if quantity_available <= 0:
            raise HTTPException(status_code=400, detail="Item out of stock")

        # Check player balance
        price = float(offer.get("price", 0))
        player_balance = float(player.get("balance", 0))

        if player_balance < price:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        # Process purchase
        new_balance = player_balance - price

        # Add item to player's inventory
        current_items = json.loads(player.get("items", "[]"))
        current_items.append(offer.get("item_name"))

        # Update player
        player_id = player.get("player_id")
        player["balance"] = new_balance
        player["items"] = json.dumps(current_items)

        new_score = recalculate_player_score(player)

        update_player(player_id, {
            "balance": new_balance,
            "items": json.dumps(current_items),
            "individual_score": new_score
        })

        # Update offer quantity
        row_index = None
        for idx, row in enumerate(offers):
            if row.get("offer_id") == offer_id:
                row_index = idx + 2  # +2 because sheets are 1-indexed and header is row 1
                break

        if row_index:
            new_quantity = quantity_available - 1
            sheet.update_cell(row_index, 4, new_quantity)  # Column 4 is quantity_available

        return {
            "success": True,
            "item_name": offer.get("item_name"),
            "price": price,
            "new_balance": new_balance,
            "message": f"Successfully purchased {offer.get('item_name')} for ${price}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

# ==================== ADMIN ENDPOINTS ====================

class CreateOfferRequest(BaseModel):
    item_name: str
    description: str
    price: float
    quantity_available: int = 1

@router.post("/admin/create-offer")
async def create_offer(request: CreateOfferRequest, player: dict = Depends(get_current_player)):
    """
    Create a new black market offer (Admin only)
    """
    if not is_admin(player.get("email")):
        raise HTTPException(status_code=403, detail="Admin access required")

    sheet = get_blackmarket_sheet()
    if sheet is None:
        raise HTTPException(status_code=500, detail="Black Market sheet not available")

    try:
        # Get all offers to determine next ID
        offers = sheet.get_all_records()
        next_id = max([o.get("offer_id", 0) for o in offers], default=0) + 1

        # Add new offer
        new_row = [
            next_id,
            request.item_name,
            request.description,
            request.quantity_available,
            request.price
        ]

        sheet.append_row(new_row)

        return {
            "success": True,
            "offer_id": next_id,
            "message": f"Created offer: {request.item_name}",
            "offer": {
                "offer_id": next_id,
                "item_name": request.item_name,
                "description": request.description,
                "price": request.price,
                "quantity_available": request.quantity_available
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create offer: {str(e)}")

@router.delete("/admin/delete-offer/{offer_id}")
async def delete_offer(offer_id: int, player: dict = Depends(get_current_player)):
    """
    Delete a black market offer (Admin only)
    """
    if not is_admin(player.get("email")):
        raise HTTPException(status_code=403, detail="Admin access required")

    sheet = get_blackmarket_sheet()
    if sheet is None:
        raise HTTPException(status_code=500, detail="Black Market sheet not available")

    try:
        offers = sheet.get_all_records()

        # Find the row index
        row_index = None
        for idx, offer in enumerate(offers):
            if offer.get("offer_id") == offer_id:
                row_index = idx + 2  # +2 because sheets are 1-indexed and header is row 1
                break

        if not row_index:
            raise HTTPException(status_code=404, detail="Offer not found")

        sheet.delete_rows(row_index)

        return {
            "success": True,
            "message": f"Deleted offer ID {offer_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete offer: {str(e)}")

@router.get("/admin/all-offers")
async def get_all_offers_admin(player: dict = Depends(get_current_player)):
    """
    Get all black market offers with full details (Admin only)
    """
    if not is_admin(player.get("email")):
        raise HTTPException(status_code=403, detail="Admin access required")

    sheet = get_blackmarket_sheet()
    if sheet is None:
        return {
            "offers": [],
            "message": "Black Market not available"
        }

    try:
        offers = sheet.get_all_records()
        return {
            "offers": offers,
            "total": len(offers),
            "market_open": is_market_open()
        }
    except Exception as e:
        return {
            "offers": [],
            "error": str(e)
        }
