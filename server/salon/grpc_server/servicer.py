"""gRPC service: one battle session played on the rules engine against Cog."""

import uuid
import grpc

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc

from salon.automata.cog import Cog
from salon.automata.interface import EndTurn, PlayCard
from salon.cards import load_deck
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.observation import observe
from salon.engine.rules import legal_actions
from salon.engine.state import BattleResult
from salon.grpc_server import convert

PLAYER_DECK = "starter"
ENEMY_DECK = "starter"
MAX_AUTOMATON_STEPS = 100 # just for safety, one automaton turn never needs this many actions


class Game(rpc.GameServicer):

    def __init__(self, player_hp=50, enemy_hp=30):
        self.session_id = str(uuid.uuid4())
        self.player_hp = player_hp
        self.enemy_hp = enemy_hp
        self.state = None # BattleState, created in StartRun below
        self.bot = None # the automaton, created in StartRun below

    def _state(self):
        return convert.state_to_proto(self.state)

    def _turn_result(self, events):
        return pb.TurnResult(events=convert.events_to_proto(events), state=self._state())
    
    def _check_session(self, request, context):
        if request.session_id != self.session_id:
            context.abort(grpc.StatusCode.NOT_FOUND, "session id does not match")

    def _check_started(self, context):
        if self.state is None:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "call StartRun first")

    def _check_ongoing(self, context):
        if self.state.result != BattleResult.ONGOING:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "battle is over")

    def _find_play(self, card_uid, connect, tab_color):
        """Match the client's request to exactly one legal PlayCard action, or None.

        When only one tab matches, the engine expects tab_color=None,
        so a color sent by the client is accepted then as well.
        """
        plays = [a for a in legal_actions(self.state)
                 if isinstance(a, PlayCard) and a.card_uid == card_uid and a.connect == connect]
        if tab_color is not None:
            plays = [a for a in plays if a.tab_color in (tab_color, None)]
        return plays[0] if len(plays) == 1 else None
            
    def _automaton_turn(self):
        """Let the automaton play until it is the player's turn again or the battle ends."""
        events = []
        for _ in range(MAX_AUTOMATON_STEPS):
            if self.state.result != BattleResult.ONGOING or self.state.player_turn:
                return events
            obs = observe(self.state, for_player=False)
            action = self.bot.choose_action(obs, legal_actions(self.state))
            self.state, new_events = apply(self.state, action)
            events += new_events
        raise RuntimeError("automaton turn did not end")

    def StartRun(self, request, context):
        self.state = create_battle(
            request.seed, load_deck(PLAYER_DECK), load_deck(ENEMY_DECK),
            player_hp=self.player_hp, enemy_hp=self.enemy_hp)
        self.bot = Cog(request.seed)
        return pb.RunState(session_id=self.session_id, battle=self._state())
    
    def PlayCard(self, request, context):
        self._check_session(request, context)
        self._check_started(context)
        self._check_ongoing(context)

        if all(card.uid != request.card_uid for card in self.state.player.hand):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "no such card in hand")
        try:
            tab_color = convert.color_from_proto(request.tab_color)
        except ValueError as err:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(err))

        action = self._find_play(request.card_uid, request.connect, tab_color)
        if action is None:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "this card cannot be played like that now")

        self.state, events = apply(self.state, action)
        return self._turn_result(events)

    def EndTurn(self, request, context):
        self._check_session(request, context)
        self._check_started(context)
        self._check_ongoing(context)

        self.state, events = apply(self.state, EndTurn())
        events += self._automaton_turn()
        return self._turn_result(events)
