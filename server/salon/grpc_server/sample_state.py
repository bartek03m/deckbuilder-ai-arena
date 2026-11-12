from salon_proto import game_pb2 as pb

START_ENERGY = 2

def make_hand() -> dict[int, pb.Card]:
    """Fresh sample hand, keyed by card uid."""
    return {
        0: pb.Card(uid=0, def_id="cios", name="Cios", colors=[pb.COLOR_RED],
                   cost=1, damage=5, tabs=[pb.Tab(color=pb.COLOR_GREEN, value=2)]),
        1: pb.Card(uid=1, def_id="blok", name="Blok", colors=[pb.COLOR_GREEN],
                   cost=1, shield=4),
    }

def build_state(hand, row, energy, round_no=1) -> pb.BattleState:
    return pb.BattleState(
        round=round_no,
        player=pb.Side(hp=50, max_hp=50, energy=energy, deck_count=5),
        enemy=pb.Side(hp=30, max_hp=30, deck_count=5),
        hand=list(hand.values()),
        row=row,
        enemy_hand=[pb.CardBack(colors=[pb.COLOR_RED]) for _ in range(5)],
    )