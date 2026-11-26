from salon_proto import game_pb2 as pb

START_ENERGY = 2        # energy in the first turn of the battle
TURN_ENERGY = 3         # energy in every later turn
PLAYER_HP = 50
ENEMY_HP = 30
ENEMY_DAMAGE = 6        # what the sample automaton deals each turn
ENEMY_CARD_UID = 100    # the sample automaton's cards get uids 100, 101, ...


def make_hand(first_uid: int = 0) -> dict[int, pb.Card]:
    """Two sample cards with uids first_uid and first_uid + 1, keyed by uid."""
    strike = pb.Card(uid=first_uid, def_id="strike", name="Strike", colors=[pb.COLOR_RED],
                   cost=1, damage=5, tabs=[pb.Tab(color=pb.COLOR_GREEN, value=2)])
    block = pb.Card(uid=first_uid + 1, def_id="block", name="Block", colors=[pb.COLOR_GREEN],
                   cost=1, shield=4)
    return {strike.uid: strike, block.uid: block}


def make_enemy_card(uid: int) -> pb.Card:
    return pb.Card(uid=uid, def_id="strike", name="Strike", colors=[pb.COLOR_RED],
                   cost=1, damage=ENEMY_DAMAGE)


def build_state(hand, row, energy, round_no=1, player_hp=PLAYER_HP, player_shield=0,
                enemy_hp=ENEMY_HP, result=pb.BATTLE_RESULT_ONGOING) -> pb.BattleState:
    return pb.BattleState(
        round=round_no,
        player=pb.Side(hp=player_hp, max_hp=PLAYER_HP, shield=player_shield,
                       energy=energy, deck_count=5),
        enemy=pb.Side(hp=enemy_hp, max_hp=ENEMY_HP, deck_count=5),
        hand=list(hand.values()),
        row=row,
        enemy_hand=[pb.CardBack(colors=[pb.COLOR_RED]) for _ in range(5)],
        result=result,
    )