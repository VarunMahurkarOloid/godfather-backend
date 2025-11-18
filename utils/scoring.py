def calculate_individual_score(
    money: float,
    missions_completed: int,
    puzzles_solved: int,
    kills_made: int,
    influence_points: float
) -> float:
    """
    Calculate individual player score based on the formula:
    individual_score = (money * 0.4) + (missions_completed * 40) +
                       (puzzles_solved * 30) + (kills_made * 100) +
                       (influence_points * 0.2)
    """
    score = (
        (money * 0.4) +
        (missions_completed * 40) +
        (puzzles_solved * 30) +
        (kills_made * 100) +
        (influence_points * 0.2)
    )
    return round(score, 2)

def recalculate_player_score(player: dict) -> float:
    """Recalculate score for a player dict"""
    return calculate_individual_score(
        money=float(player.get("balance", 0)),
        missions_completed=int(player.get("missions_completed", 0)),
        puzzles_solved=int(player.get("puzzles_solved", 0)),
        kills_made=int(player.get("kills_made", 0)),
        influence_points=float(player.get("influence_points", 0))
    )
