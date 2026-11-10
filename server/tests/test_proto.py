from salon_proto import game_pb2 as pb


def test_battle_state_roundtrip():
    state = pb.BattleState(round=1)
    state.player.hp = 50
    state.hand.append(pb.Card(uid=0, def_id="cios", colors=[pb.COLOR_RED], cost=1, damage=5))

    # object -> bytes -> object (simulation of work between python server and c# client)
    data = state.SerializeToString()          
    back = pb.BattleState.FromString(data)    

    assert back.player.hp == 50
    assert back.hand[0].def_id == "cios"