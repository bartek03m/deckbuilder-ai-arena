using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Grpc.Core;
using Salon.Proto;
using ProtoCard = Salon.Proto.Card;
using ProtoColor = Salon.Proto.Color;

// Fake server for working on the client without Python.
// Returns sample data and every kind of event so the UI can be built before the engine exists.
// These are NOT game rules (those live only in the Python engine), just a fixed script.
public sealed class MockGameService : IGameService
{
	private const string MockSessionId = "mock-session";

	private readonly List<ProtoCard> _hand = new();
	private readonly List<ProtoCard> _row = new();
	private int _nextUid;
	private int _energy;
	private int _round;
	private int _playerHp;
	private int _enemyHp;
	private BattleResult _result;

	public Task<RunState> StartRunAsync(long seed)
	{
		_nextUid = 0;
		_energy = 2;
		_round = 1;
		_result = BattleResult.Ongoing;
		_playerHp = 50;
		_enemyHp = 30;
		_row.Clear();
		DealSampleHand();
		return Task.FromResult(new RunState { SessionId = MockSessionId, Battle = BuildState() });
	}

	public Task<TurnResult> PlayCardAsync(string sessionId, int cardUid, bool connect = false, ProtoColor tabColor = ProtoColor.Unspecified)
	{
		if (sessionId != MockSessionId)
			return Fail<TurnResult>(StatusCode.NotFound, "session id does not match");
		
		if(_result != BattleResult.Ongoing)
			return Fail<TurnResult>(StatusCode.FailedPrecondition, "battle is over");

		var card = _hand.FirstOrDefault(c => c.Uid == cardUid);
		if (card == null)
			return Fail<TurnResult>(StatusCode.InvalidArgument, "no such card in hand");
		if (card.Cost > _energy)
			return Fail<TurnResult>(StatusCode.FailedPrecondition, "not enough available energy");

		_hand.Remove(card);
		_row.Add(card);
		_energy -= card.Cost;

		var result = new TurnResult();
		result.Events.Add(new Event { CardPlayed = new CardPlayed { ByPlayer = true, Card = card } });
		foreach (var tab in card.Tabs) // sample event so the UI has something to show
			result.Events.Add(new Event { TabActivated = new TabActivated { CardUid = card.Uid, Tab = tab } });
			result.Events.Add(new Event { EnergyChanged = new EnergyChanged { Player = true, Value = _energy } });
		result.State = BuildState();
		return Task.FromResult(result);
	}

	public Task<TurnResult> EndTurnAsync(string sessionId)
	{
		if (sessionId != MockSessionId)
			return Fail<TurnResult>(StatusCode.NotFound, "session id does not match");
		if (_result != BattleResult.Ongoing)
			return Fail<TurnResult>(StatusCode.FailedPrecondition, "battle is over");

		const int damageToEnemy = 12;
		const int damageToPlayer = 3;
		var result = new TurnResult();

		// Player attack 
		_enemyHp = Math.Max(0, _enemyHp - damageToEnemy);
		result.Events.Add(new Event { Damage = new Damage { ToPlayer = false, Amount = damageToEnemy } });
		if (_enemyHp == 0)
			return Finish(result, BattleResult.Won);
		DealSampleHand();
		result.Events.Add(new Event { CardsDrawn = new CardsDrawn { Player = true, Count = _hand.Count } });

		// End of player turn
		var discarded = new CardsDiscarded { Player = true };
		discarded.CardUids.Add(_row.Select(c => c.Uid));
		result.Events.Add(new Event { CardsDiscarded = discarded });
		_row.Clear();

		// Enemy turn
		result.Events.Add(new Event { EnergyChanged = new EnergyChanged { Player = false, Value = 3 } });
		var enemyCard = new ProtoCard
		{
			Uid = _nextUid++, DefId = "strike", Name = "Strike", Colors = { ProtoColor.Red }, Cost = 1, Damage = damageToPlayer,
		};
		result.Events.Add(new Event { CardPlayed = new CardPlayed { ByPlayer = false, Card = enemyCard } });
		_playerHp = Math.Max(0, _playerHp - damageToPlayer);
		result.Events.Add(new Event { Damage = new Damage { ToPlayer = true, Amount = damageToPlayer } });
		if (_playerHp == 0)
			return Finish(result, BattleResult.Lost);
		result.Events.Add(new Event { CardsDrawn = new CardsDrawn { Player = false, Count = 3 } });
		var enemyDiscarded = new CardsDiscarded { Player = false };
		enemyDiscarded.CardUids.Add(enemyCard.Uid);
		result.Events.Add(new Event { CardsDiscarded = enemyDiscarded });

		// Start of the new player turn
		_energy = 3;
		_round++;
		result.Events.Add(new Event { EnergyChanged = new EnergyChanged { Player = true, Value = _energy } });

		result.State = BuildState();
		return Task.FromResult(result);
	}

		private Task<TurnResult> Finish(TurnResult result, BattleResult outcome)
	{
		_result = outcome;
		result.Events.Add(new Event { BattleEnded = new BattleEnded { Result = outcome } });
		result.State = BuildState();
		return Task.FromResult(result);
	}

	public void Dispose() { }

	private void DealSampleHand()
	{
		_hand.Clear();
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "strike", Name = "Strike", Colors = { ProtoColor.Red },
			Cost = 1, Damage = 5, Tabs = { new Tab { Color = ProtoColor.Green, Value = 2 } },
		});
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "block", Name = "Block", Colors = { ProtoColor.Green },
			Cost = 1, Shield = 4,
		});
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "ponder", Name = "Ponder", Colors = { ProtoColor.Blue },
			Cost = 1, Draw = 2, Tabs = { new Tab { Color = ProtoColor.Red, Value = 1 } },
		});
	}

	private BattleState BuildState()
	{
		var state = new BattleState
		{
			Round = _round,
			Result = _result,
			Player = new Side { Hp = _playerHp, MaxHp = 50, Energy = _energy, DeckCount = 7 },
			Enemy = new Side { Hp = _enemyHp, MaxHp = 30, DeckCount = 8 },
		};
		state.Hand.Add(_hand);
		state.Row.Add(_row);
		state.EnemyHand.Add(new CardBack { Colors = { ProtoColor.Red } });
		state.EnemyHand.Add(new CardBack { Colors = { ProtoColor.Green } });
		state.EnemyHand.Add(new CardBack { Colors = { ProtoColor.Blue } });
		state.EnemyHand.Add(new CardBack { Colors = { ProtoColor.Red, ProtoColor.Blue } });
		return state;
	}

	private static Task<T> Fail<T>(StatusCode code, string detail) =>
		Task.FromException<T>(new RpcException(new Status(code, detail)));
}