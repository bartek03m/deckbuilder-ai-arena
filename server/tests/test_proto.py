from salon_proto import game_pb2 as pb


def test_battle_state_roundtrip():
    state = pb.BattleState(round=1)
    state.player.hp = 50
    state.hand.append(pb.Card(uid=0, def_id="strike", colors=[pb.COLOR_RED], cost=1, damage=5))

    # object -> bytes -> object (simulation of work between python server and c# client)
    data = state.SerializeToString()          
    back = pb.BattleState.FromString(data)    

    assert back.player.hp == 50
    assert back.hand[0].def_id == "strike"

def test_v1_messages_roundtrip():
    discarded = pb.Event(cards_discarded=pb.CardsDiscarded(player=True, card_uids=[0, 3]))
    back = pb.Event.FromString(discarded.SerializeToString())
    assert back.WhichOneof("kind") == "cards_discarded"
    assert list(back.cards_discarded.card_uids) == [0, 3]

    energy = pb.Event(energy_changed=pb.EnergyChanged(player=False, value=3))
    back = pb.Event.FromString(energy.SerializeToString())
    assert back.energy_changed.value == 3 and back.energy_changed.player is False

    ended = pb.Event(battle_ended=pb.BattleEnded(result=pb.BATTLE_RESULT_WON))
    back = pb.Event.FromString(ended.SerializeToString())
    assert back.battle_ended.result == pb.BATTLE_RESULT_WON

    state = pb.BattleState(result=pb.BATTLE_RESULT_LOST)
    assert pb.BattleState.FromString(state.SerializeToString()).result == pb.BATTLE_RESULT_LOST


def test_battle_result_defaults_to_ongoing():
    assert pb.BattleState().result == pb.BATTLE_RESULT_ONGOING