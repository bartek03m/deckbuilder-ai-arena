import uuid
import grpc

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc
from salon.grpc_server import sample_state

class Game(rpc.GameServicer):

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self._reset()

    def _reset(self):
        self.energy = sample_state.START_ENERGY
        self.hand = sample_state.make_hand()
        self.row = []
        self.round_no = 1

    def _state(self):
        return sample_state.build_state(self.hand, self.row, self.energy, self.round_no)

    def _check_session(self, request, context):
        if request.session_id != self.session_id:
            context.abort(grpc.StatusCode.NOT_FOUND, "session id does not match")

    def StartRun(self, request, context):
        self._reset()
        return pb.RunState(session_id=self.session_id, battle=self._state())
    
    def PlayCard(self, request, context):
        #validation
        self._check_session(request, context)

        if request.card_uid not in self.hand:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "no such card in hand")
        
        card = self.hand[request.card_uid]
        if card.cost > self.energy:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "not enough available energy")

        del self.hand[request.card_uid]
        self.energy -= card.cost
        self.row.append(card)

        event = pb.Event(card_played=pb.CardPlayed(by_player=True, card=card))
        return pb.TurnResult(events=[event], state=self._state())

    def EndTurn(self, request, context):
        self._check_session(request, context)

        dmg = sum(card.damage for card in self.row)
        event = pb.Event(damage=pb.Damage(to_player=False, amount=dmg))
        self.row = []
        self.energy = 3
        self.round_no += 1
        return pb.TurnResult(events=[event], state=self._state())
