import uuid
import grpc

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc
from salon.grpc_server import sample_state

# small helpers so the code below stays readable
def _card_played(by_player, card):
    return pb.Event(card_played=pb.CardPlayed(by_player=by_player, card=card))

def _tab_activated(card_uid, tab):
    return pb.Event(tab_activated=pb.TabActivated(card_uid=card_uid, tab=tab))

def _damage(to_player, amount, absorbed=0):
    return pb.Event(damage=pb.Damage(to_player=to_player, amount=amount, absorbed=absorbed))

def _shield_changed(player, value):
    return pb.Event(shield_changed=pb.ShieldChanged(player=player, value=value))

def _cards_drawn(player, count):
    return pb.Event(cards_drawn=pb.CardsDrawn(player=player, count=count))

def _energy_changed(player, value):
    return pb.Event(energy_changed=pb.EnergyChanged(player=player, value=value))

def _cards_discarded(player, card_uids):
    return pb.Event(cards_discarded=pb.CardsDiscarded(player=player, card_uids=card_uids))

class Game(rpc.GameServicer):

    def __init__(self, player_hp=sample_state.PLAYER_HP, enemy_hp=sample_state.ENEMY_HP):
        self.session_id = str(uuid.uuid4())
        self.start_player_hp = player_hp    # default values are in sample_state
        self.start_enemy_hp = enemy_hp
        self._reset()

    def _reset(self):
        self.energy = sample_state.START_ENERGY
        self.hand = sample_state.make_hand()
        self.next_uid = 2   # 2 because make_hand makes 2 cards at once right now in sample_state (its temporary)
        self.row = []
        self.round_no = 1
        self.player_hp = self.start_player_hp
        self.enemy_hp = self.start_enemy_hp
        self.player_shield = 0                         
        self.result = pb.BATTLE_RESULT_ONGOING

    def _state(self):
        return sample_state.build_state(self.hand, self.row, self.energy, self.round_no,
        player_hp=self.player_hp, player_shield=self.player_shield,
        enemy_hp=self.enemy_hp, result=self.result)

    def _check_session(self, request, context):
        if request.session_id != self.session_id:
            context.abort(grpc.StatusCode.NOT_FOUND, "session id does not match")

    def _check_ongoing(self, context):
        if self.result != pb.BATTLE_RESULT_ONGOING:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "battle is over")

    def _end_battle(self, result, events):
        self.result = result
        events.append(pb.Event(battle_ended=pb.BattleEnded(result=result)))
        return pb.TurnResult(events=events, state=self._state())

    def _draw_cards(self):
        new = sample_state.make_hand(self.next_uid)
        self.next_uid += len(new)
        self.hand.update(new)
        return list(new.values())

    def StartRun(self, request, context):
        self._reset()
        return pb.RunState(session_id=self.session_id, battle=self._state())
    
    def PlayCard(self, request, context):
        #validation
        self._check_session(request, context)
        self._check_ongoing(context)

        if request.card_uid not in self.hand:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "no such card in hand")
        
        card = self.hand[request.card_uid]
        if card.cost > self.energy:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "not enough available energy")

        if self.row:    # to remember the last card played
            previous = self.row[-1]
        else:
            previous = None

        del self.hand[request.card_uid]
        self.energy -= card.cost
        self.row.append(card)

        events = [_card_played(True, card)]
        if request.connect and previous is not None and previous.tabs:
            events.append(_tab_activated(previous.card_uid, previous.tabs[0])) # TODO: you need to check which tab is the one activated its not always 0
        events.append(_energy_changed(True, self.energy)) # new amount of energy after played card

        return pb.TurnResult(events=events, state=self._state())

    def EndTurn(self, request, context):
        self._check_session(request, context)
        self._check_ongoing(context)
        events = []

        damage = sum(card.damage for card in self.row)
        shield = sum(card.shield for card in self.row)

        # TODO: 1. start counting tabs into damage and shield after first round for player
        # TODO: 2. include enemy shield in damage calculations
        
        if damage > 0:
            self.enemy_hp = max(0, self.enemy_hp - damage)
            events.append(_damage(False, damage))
            if self.enemy_hp == 0:
                return self._end_battle(pb.BATTLE_RESULT_WON, events)
        if shield > 0:
            self.player_shield += shield
            events.append(_shield_changed(True, self.player_shield))

        drawn = self._draw_cards()
        events.append(_cards_drawn(True, len(drawn)))

        discarded = [card.uid for card in self.row]
        self.row = []
        if discarded:
            events.append(_cards_discarded(True, discarded))

        # bot turn -> player == false
        events.append(_energy_changed(False, sample_state.TURN_ENERGY))
        enemy_card = sample_state.make_enemy_card(sample_state.ENEMY_CARD_UID + self.round_no)
        events.append(_card_played(False, enemy_card))

        absorbed = min(self.player_shield, enemy_card.damage)
        self.player_hp = max(0, self.player_hp - (enemy_card.damage - absorbed))
        events.append(_damage(True, enemy_card.damage, absorbed))
        if self.player_hp == 0:
            return self._end_battle(pb.BATTLE_RESULT_LOST, events)

        events.append(_cards_drawn(False, 1))
        events.append(_cards_discarded(False, [enemy_card.uid]))

        self.round_no += 1
        
        if self.player_shield > 0:
            self.player_shield = 0
            events.append(_shield_changed(True, self.player_shield))

        self.energy = sample_state.TURN_ENERGY
        events.append(_energy_changed(True, self.energy))

        return pb.TurnResult(events=events, state=self._state())
