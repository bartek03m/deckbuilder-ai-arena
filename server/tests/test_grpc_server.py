import grpc
import pytest

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc
from salon.grpc_server.main import create_server


@pytest.fixture
def stub():
    server, port = create_server("127.0.0.1:0")   # 0 = any free port
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    yield rpc.GameStub(channel)
    channel.close()
    server.stop(0)


def test_start_run_returns_battle(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    assert run.session_id
    assert run.battle.player.hp == 50
    assert len(run.battle.hand) == 2


def test_play_card_moves_card_to_row(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    start_energy = run.battle.player.energy
    result = stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    assert len(result.state.row) == 1
    assert len(result.state.hand) == 1
    assert result.state.player.energy == start_energy - 1   # Cios costs 1
    assert result.events[0].WhichOneof("kind") == "card_played"


def test_play_unknown_card_is_rejected(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    with pytest.raises(grpc.RpcError) as err:
        stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=99))
    assert err.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_wrong_session_is_rejected(stub):
    stub.StartRun(pb.StartRunRequest(seed=1))
    with pytest.raises(grpc.RpcError) as err:
        stub.EndTurn(pb.EndTurnRequest(session_id="wrong"))
    assert err.value.code() == grpc.StatusCode.NOT_FOUND


def test_end_turn_next_round(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    result = stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))
    assert result.state.round == 2
    assert len(result.state.row) == 0
    assert result.events[0].damage.amount == 5