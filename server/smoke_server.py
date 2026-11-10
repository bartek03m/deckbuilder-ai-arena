from concurrent import futures

import grpc

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc

class Game(rpc.GameServicer):
    def __init__(self):
        self.energy = 3
        self.hand = {
            0: pb.Card(uid=0, def_id="cios", name="Cios", colors=[pb.COLOR_RED], cost=1, damage=5,
                       tabs=[pb.Tab(color=pb.COLOR_GREEN, value=2)]),
            1: pb.Card(uid=1, def_id="blok", name="Blok", colors=[pb.COLOR_GREEN], cost=1, shield=4),
        }
        self.row = []

    def _state(self):
        return pb.BattleState(
            round = 1,
            player=pb.Side(hp=50, max_hp=50, energy=self.energy, deck_count=5),
            enemy=pb.Side(hp=30, max_hp=30, deck_count=5),
            hand=list(self.hand.values()),
            row=self.row,
            enemy_hand=[pb.CardBack(colors=[pb.COLOR_RED]) for _ in range(5)],
        )
    
    def StartRun(self, request, context):
        return pb.RunState(session_id="test", battle=self._state())

    def PlayCard(self, request, context):
        if request.card_uid not in self.hand:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "no such card in hand")
        card = self.hand.pop(request.card_uid)
        self.energy -= card.cost
        self.row.append(card)
        event = pb.Event(card_played=pb.CardPlayed(by_player=True, card=card))
        return pb.TurnResult(events=[event], state=self._state())

    # EndTurn not overridden: the generated base returns UNIMPLEMENTED

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_GameServicer_to_server(Game(), server)
    server.add_insecure_port("127.0.0.1:50051")
    server.start()
    print("server running on 127.0.0.1:50051 (Ctrl+C to stop)")
    server.wait_for_termination()

if __name__ == "__main__":
    main()