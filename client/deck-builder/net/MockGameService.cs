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

	public Task<RunState> StartRunAsync(long seed)
	{
		_nextUid = 0;
		_energy = 2;
		_round = 1;
		_playerHp = 50;
		_enemyHp = 30;
		_row.Clear();
		DealSampleHand();
		return Task.FromResult(new RunState { SessionId = MockSessionId, Battle = BuildState() });
	}

	public Task<TurnResult> PlayCardAsync(string sessionId, int cardUid)
	{
		if (sessionId != MockSessionId)
			return Fail<TurnResult>(StatusCode.NotFound, "session id does not match");

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
		result.State = BuildState();
		return Task.FromResult(result);
	}

	public Task<TurnResult> EndTurnAsync(string sessionId)
	{
		if (sessionId != MockSessionId)
			return Fail<TurnResult>(StatusCode.NotFound, "session id does not match");

		const int damageToEnemy = 5;
		const int damageToPlayer = 3;
		_enemyHp = Math.Max(0, _enemyHp - damageToEnemy);
		_playerHp = Math.Max(0, _playerHp - damageToPlayer);
		_row.Clear();
		_energy = 3;
		_round++;
		DealSampleHand();

		var result = new TurnResult();
		result.Events.Add(new Event { Damage = new Damage { ToPlayer = false, Amount = damageToEnemy } });
		result.Events.Add(new Event { ShieldChanged = new ShieldChanged { Player = false, Value = 2 } });
		result.Events.Add(new Event { Damage = new Damage { ToPlayer = true, Amount = damageToPlayer } });
		result.Events.Add(new Event { CardsDrawn = new CardsDrawn { Player = true, Count = _hand.Count } });
		result.State = BuildState();
		return Task.FromResult(result);
	}

	public void Dispose() { }

	private void DealSampleHand()
	{
		_hand.Clear();
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "cios", Name = "Cios", Colors = { ProtoColor.Red },
			Cost = 1, Damage = 5, Tabs = { new Tab { Color = ProtoColor.Green, Value = 2 } },
		});
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "blok", Name = "Blok", Colors = { ProtoColor.Green },
			Cost = 1, Shield = 4,
		});
		_hand.Add(new ProtoCard
		{
			Uid = _nextUid++, DefId = "namysl", Name = "Namysł", Colors = { ProtoColor.Blue },
			Cost = 1, Draw = 2, Tabs = { new Tab { Color = ProtoColor.Red, Value = 1 } },
		});
	}

	private BattleState BuildState()
	{
		var state = new BattleState
		{
			Round = _round,
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