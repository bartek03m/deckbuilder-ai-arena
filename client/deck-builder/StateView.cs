using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using Grpc.Core;
using Salon.Proto;
using ProtoCard = Salon.Proto.Card;
using ProtoEvent = Salon.Proto.Event;
using ProtoSide = Salon.Proto.Side;

public partial class StateView : Control
{
	private const int MaxLogLines = 15;

	[Export] public bool UseMock { get; set; } = true;
	[Export] public string ServerAddress { get; set; } = "http://127.0.0.1:50051";

	private IGameService _service;
	private string _sessionId = "";
	private readonly List<string> _log = new();

	private Label _connection;
	private Label _enemy;
	private Label _enemyHand;
	private Label _row;
	private Label _player;
	private HBoxContainer _hand;
	private Button _endTurn;
	private Label _events;

	public override async void _Ready()
	{
		_connection = GetNode<Label>("%Connection");
		_enemy = GetNode<Label>("%Enemy");
		_enemyHand = GetNode<Label>("%EnemyHand");
		_row = GetNode<Label>("%Row");
		_player = GetNode<Label>("%Player");
		_hand = GetNode<HBoxContainer>("%Hand");
		_endTurn = GetNode<Button>("%EndTurn");
		_events = GetNode<Label>("%Events");

		_endTurn.Pressed += OnEndTurnPressed;

		_service = UseMock ? new MockGameService() : new GrpcGameService(ServerAddress);
		_connection.Text = UseMock ? "Mock server (no Python)" : $"Server: {ServerAddress}";

		await RunRequest(async () =>
		{
			var run = await _service.StartRunAsync(42);
			_sessionId = run.SessionId;
			AddLog($"Run started, session {run.SessionId}");
			ShowState(run.Battle);
		});
	}

	public override void _ExitTree()
	{
		_service?.Dispose();
		_service = null;
	}

	private async void OnCardPressed(int cardUid) => await RunRequest(async () =>
	{
		ShowResult(await _service.PlayCardAsync(_sessionId, cardUid));
	});

	private async void OnEndTurnPressed() => await RunRequest(async () =>
	{
		ShowResult(await _service.EndTurnAsync(_sessionId));
	});

	private async Task RunRequest(Func<Task> request)
	{
		SetButtonsDisabled(true);
		try
		{
			await request();
		}
		catch (RpcException ex)
		{
			AddLog($"gRPC error: {ex.StatusCode} {ex.Status.Detail}");
		}
		finally
		{
			SetButtonsDisabled(false);
		}
	}

	private void ShowResult(TurnResult result)
	{
		foreach (var e in result.Events)
			AddLog(FormatEvent(e));
		ShowState(result.State);
	}

	private void ShowState(BattleState state)
	{
		if (state == null)
			return;

		_enemy.Text = $"Enemy:  {FormatSide(state.Enemy)}";
		_enemyHand.Text = $"Enemy hand ({state.EnemyHand.Count}): " +
			string.Join(", ", state.EnemyHand.Select(back => string.Join("/", back.Colors)));
		_row.Text = "Row: " + (state.Row.Count == 0 ? "empty" : string.Join(", ", state.Row.Select(c => c.Name)));
		_player.Text = $"Round {state.Round}   Player:  {FormatSide(state.Player)}";

		foreach (Node child in _hand.GetChildren())
			child.QueueFree();

		foreach (var card in state.Hand)
		{
			var button = new Button { Text = FormatCard(card) };
			int uid = card.Uid;
			button.Pressed += () => OnCardPressed(uid);
			_hand.AddChild(button);
		}
	}

	private void SetButtonsDisabled(bool disabled)
	{
		_endTurn.Disabled = disabled;
		foreach (Node child in _hand.GetChildren())
			if (child is Button button)
				button.Disabled = disabled;
	}

	private void AddLog(string line)
	{
		_log.Add(line);
		if (_log.Count > MaxLogLines)
			_log.RemoveAt(0);
		_events.Text = "Events:\n" + string.Join("\n", _log);
	}

	private static string FormatSide(ProtoSide side) =>
		side == null
			? "-"
			: $"HP {side.Hp}/{side.MaxHp}   Shield {side.Shield}   Energy {side.Energy}   Deck {side.DeckCount}   Discard {side.DiscardCount}";

	private static string FormatCard(ProtoCard card)
	{
		var lines = new List<string> { card.Name, $"cost {card.Cost} | {string.Join("/", card.Colors)}" };
		if (card.Damage > 0) lines.Add($"damage {card.Damage}");
		if (card.Shield > 0) lines.Add($"shield {card.Shield}");
		if (card.Draw > 0) lines.Add($"draw {card.Draw}");
		foreach (var tab in card.Tabs)
			lines.Add($"tab {tab.Color} +{tab.Value}");
		return string.Join("\n", lines);
	}

	private static string FormatEvent(ProtoEvent e) => e.KindCase switch
	{
		ProtoEvent.KindOneofCase.CardPlayed =>
			$"{(e.CardPlayed.ByPlayer ? "Player" : "Enemy")} played {e.CardPlayed.Card?.Name}",
		ProtoEvent.KindOneofCase.TabActivated =>
			$"Tab {e.TabActivated.Tab?.Color} +{e.TabActivated.Tab?.Value} activated (card {e.TabActivated.CardUid})",
		ProtoEvent.KindOneofCase.Damage =>
			$"{(e.Damage.ToPlayer ? "Player" : "Enemy")} takes {e.Damage.Amount} damage ({e.Damage.Absorbed} absorbed)",
		ProtoEvent.KindOneofCase.ShieldChanged =>
			$"{(e.ShieldChanged.Player ? "Player" : "Enemy")} shield is now {e.ShieldChanged.Value}",
		ProtoEvent.KindOneofCase.CardsDrawn =>
			$"{(e.CardsDrawn.Player ? "Player" : "Enemy")} drew {e.CardsDrawn.Count} cards",
		_ => $"Unknown event: {e.KindCase}",
	};
}