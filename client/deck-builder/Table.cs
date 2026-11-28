using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using Salon.Proto;
using ProtoCard = Salon.Proto.Card;
using ProtoSide = Salon.Proto.Side;
using Grpc.Core;
using ProtoEvent = Salon.Proto.Event;
public partial class Table : Control
{
	// CARD SCENE
	[Export] public PackedScene CardScene { get; set; }
	// SERVER
	[Export] public bool UseMock {  get; set; } = true;
	[Export] public string ServerAddress { get; set; } = "http://127.0.0.1:50051";

	// Pause after each event so the player can follow what happens
	[Export] public float EventDelay { get; set;} = 0.3f;

	//Emitted when the BattleEnded event is played
	[Signal] public delegate void BattleFinishedEventHandler(int result);

	// PLAYER AND ENEMY STATS
	private Label _playerHpLabel;
	private Label _playerShieldLabel;
	private Label _playerEnergyLabel;

	private Label _enemyNameLabel;
	private Label _enemyHpLabel;
	private Label _enemyShieldLabel;
	private Label _enemyEnergyLabel;
	private Label _roundLabel;

	// DECK AND DISCARD PILE AND ATTACK BUTTON
	private Button _deckPileButton;
	private Button _discardPileButton;
	private Button _attackButton;

	// PLAYER AND ENEMY HANDS
	private HBoxContainer _playerHandContainer;
	private HBoxContainer _enemyHandContainer;
	private HBoxContainer _rowContainer;

	// PLAYER PREVIEW STATS
	private Label _damagePreviewLabel;
	private Label _shieldPreviewLabel;
	private Label _drawPreviewLabel;

	// SESSION
	private IGameService _service;
	private string _sessionId = "";
	private EventQueue _events;
	private bool _battleOver;

	public bool IsBusy => _events?.IsBusy ?? false;
	public bool IsBattleOver => _battleOver;

	//Input
	//True from sending a request until its response has been played
	private bool _requestPending;

	//Player can act only when no request is waiting
	private bool CanAct => !_requestPending && !IsBusy && !_battleOver;

	// _Ready 
	public override async void _Ready()
	{
		CardScene ??= GD.Load<PackedScene>("res://card.tscn");

		_playerHpLabel       = GetNode<Label>("BottomBar/PlayerStats/StatsVBox/HpLabel");
		_playerShieldLabel   = GetNode<Label>("BottomBar/PlayerStats/StatsVBox/ShieldLabel");
		_playerEnergyLabel   = GetNode<Label>("BottomBar/PlayerStats/StatsVBox/EnergyLabel");

		_enemyNameLabel      = GetNode<Label>("TopBar/EnemyStats/EnemyStatsVBox/EnemyNameLabel");
		_enemyHpLabel        = GetNode<Label>("TopBar/EnemyStats/EnemyStatsVBox/EnemyHpLabel");
		_enemyShieldLabel    = GetNode<Label>("TopBar/EnemyStats/EnemyStatsVBox/EnemyShieldLabel");
		_enemyEnergyLabel    = GetNode<Label>("TopBar/EnemyStats/EnemyStatsVBox/EnemyEnergyLabel");
		_roundLabel          = GetNode<Label>("TopBar/RoundPanel/RoundLabel");

		_deckPileButton      = GetNode<Button>("MiddleArea/DeckPile");
		_discardPileButton   = GetNode<Button>("MiddleArea/DiscardPile");
		_attackButton        = GetNode<Button>("MiddleArea/AttackButton");
		_attackButton.Pressed += OnAttackPressed;

		_playerHandContainer = GetNode<HBoxContainer>("BottomBar/PlayerHand");
		_enemyHandContainer  = GetNode<HBoxContainer>("TopBar/EnemyHand");
		_rowContainer        = GetNode<HBoxContainer>("MiddleArea/RowContainer");

		_events = new EventQueue(PlayEventAsync, UpdateState);
		_events.Idle += RefreshInput;

		// SERVICE: mock (no Python) or real gRPC server
		_service = UseMock ? new MockGameService() : new GrpcGameService(ServerAddress);
		try
		{
			var run = await _service.StartRunAsync(42);
			_sessionId = run.SessionId;
			UpdateState(run.Battle);
		}
		catch (RpcException ex)
		{
			GD.PushError($"StartRun failed: {ex.StatusCode} {ex.Status.Detail}");
		}
	}

	public override void _ExitTree()
	{
		_service?.Dispose();
		_service = null;
	}

	public Task ShowTurnResultAsync(TurnResult result) => _events.EnqueueAsync(result);

	// Player input
	// drop on the last card in the row = connect it; drop anywhere else on the row = start a new chain
	//click = play without a connection
	private async void OnHandCardClicked(int cardUid) => await TryPlayCardAsync(cardUid, false);

	private async void OnHandCardDropped(int cardUid, Vector2 globalPosition)
	{
		var mouse = GetGlobalMousePosition();
		if (!_rowContainer.GetGlobalRect().HasPoint(mouse))
		{
			ReturnCardsToHand();
			return;
		}

		var lastInRow = _rowContainer.GetChildren().OfType<Card>().LastOrDefault();
		bool connect = lastInRow != null && lastInRow.GetGlobalRect().HasPoint(mouse);
		await TryPlayCardAsync(cardUid, connect);
	}

	private async Task TryPlayCardAsync(int cardUid, bool connect)
	{
		bool played = await RunRequestAsync(() => _service.PlayCardAsync(_sessionId, cardUid, connect));
		if (!played)
			ReturnCardsToHand();
	}

	// Attack. the server resolver the row and plays automaton turn (EndTurn).
	private async void OnAttackPressed() => await RunRequestAsync(() => _service.EndTurnAsync(_sessionId));

	private async Task<bool> RunRequestAsync(Func<Task<TurnResult>> request)
	{
		if (!CanAct)
			return false;

		_requestPending = true;
		RefreshInput();
		try
		{
			var result = await request();
			await ShowTurnResultAsync(result);
			return true;
		}
		catch (RpcException ex)
		{
			GD.PushWarning($"Server rejected the move: {ex.StatusCode} {ex.Status.Detail}");
			return false;
		}
		finally
		{
			_requestPending = false;
			RefreshInput();
		}
	}

	// A dragged card stays where it was dropped; sorting puts every card back to its place in a row.
	private void ReturnCardsToHand() => _playerHandContainer.QueueSort();

	// locks or unlocks the attack button and the cards in hadn
	private void RefreshInput()
	{
		bool canAct = CanAct;
		_attackButton.Disabled = !canAct;
		foreach(var card in _playerHandContainer.GetChildren().OfType<Card>())
			card.MouseFilter = canAct ? MouseFilterEnum.Stop : MouseFilterEnum.Ignore;
	}

	// UPDATE STATE
	public void UpdateState(BattleState state)
	{
		if (state == null) return;

		_battleOver = state.Result != BattleResult.Ongoing;
		UpdateStats(state);
		UpdateCards(state);
		RefreshInput();
	}

	// PLAY ONE EVENT
	private async Task PlayEventAsync(ProtoEvent e)
	{
		GD.Print($"[event] {e}");

		switch (e.KindCase)
		{
			case ProtoEvent.KindOneofCase.CardPlayed:
				OnCardPlayed(e.CardPlayed);
				break;
			case ProtoEvent.KindOneofCase.ShieldChanged:
				SetShieldLabel(e.ShieldChanged.Player, e.ShieldChanged.Value);
				break;
			case ProtoEvent.KindOneofCase.EnergyChanged:
				SetEnergyLabel(e.EnergyChanged.Player, e.EnergyChanged.Value);
				break;
			case ProtoEvent.KindOneofCase.CardsDiscarded:
				RemoveFromRow(e.CardsDiscarded.CardUids);
				break;
			case ProtoEvent.KindOneofCase.BattleEnded:
				_battleOver = true;
				EmitSignal(SignalName.BattleFinished, (int)e.BattleEnded.Result);
				break;
		}

		if (EventDelay > 0)
			await ToSignal(GetTree().CreateTimer(EventDelay), SceneTreeTimer.SignalName.Timeout);
	}
	private void OnCardPlayed(CardPlayed played)
	{
		if (played.Card == null) return;

		if (played.ByPlayer)
		{
			var inHand = FindCard(_playerHandContainer, played.Card.Uid);
			if (inHand != null)
				RemoveCardNode(_playerHandContainer, inHand);
		}
		else if (_enemyHandContainer.GetChildCount() > 0)
		{
			RemoveCardNode(_enemyHandContainer, _enemyHandContainer.GetChild(0));
		}

		AddRowCard(played.Card);
	}

	//Cards in the row only show what was played, ignore the mouse (later changed when undo comes probably...)
	private void AddRowCard(ProtoCard data)
	{
		var cardInstance = CardScene.Instantiate<Card>();
		_rowContainer.AddChild(cardInstance);
		cardInstance.SetCardData(data);
		cardInstance.MouseFilter = MouseFilterEnum.Ignore;
	}

	private void RemoveFromRow(IEnumerable<int> cardUids)
	{
		foreach (var uid in cardUids)
		{
			var card = FindCard(_rowContainer, uid);
			if (card != null)
				RemoveCardNode(_rowContainer, card);
		}
	}

	private void SetShieldLabel(bool player, int value)
	{
		var label = player ? _playerShieldLabel : _enemyShieldLabel;
		label.Text = $"Shield: {value}";
	}

	private void SetEnergyLabel(bool player, int value)
	{
		var label = player ? _playerEnergyLabel : _enemyEnergyLabel;
		label.Text = $"Energy: {value}";
	}

	private static Card FindCard(Node container, int uid) =>
		container.GetChildren().OfType<Card>().FirstOrDefault(c => c.CardUid == uid);
	
	private static void RemoveCardNode(Node container, Node card)
	{
		container.RemoveChild(card);
		card.QueueFree();
	}

	private void UpdateStats(BattleState state)
	{
		// PLAYER STATS
		_playerHpLabel.Text     = $"HP: {state.Player.Hp} / {state.Player.MaxHp}";
		_playerShieldLabel.Text = $"Shield: {state.Player.Shield}";
		_playerEnergyLabel.Text = $"Energy: {state.Player.Energy}";

		// DECK AND DISCARD PILE
		_deckPileButton.Text    = $"Deck\n({state.Player.DeckCount})";
		_discardPileButton.Text = $"Discard\n({state.Player.DiscardCount})";

		// ROUND
		_roundLabel.Text        = $"Round {state.Round}";

		// ENEMY STATS
		_enemyHpLabel.Text      = $"HP: {state.Enemy.Hp} / {state.Enemy.MaxHp}";
		_enemyShieldLabel.Text  = $"Shield: {state.Enemy.Shield}";
		_enemyNameLabel.Text    = "Bot";
		_enemyEnergyLabel.Text = $"Energy: {state.Enemy.Energy}";
	}

	private void UpdateCards(BattleState state) { 
		ClearContainer(_playerHandContainer);
		ClearContainer(_enemyHandContainer);
		ClearContainer(_rowContainer);

		// PLAYER HAND
		foreach (var c in state.Hand) {
			var cardInstance = CardScene.Instantiate<Card>();
			_playerHandContainer.AddChild(cardInstance);
			cardInstance.SetCardData(c);
			cardInstance.SizeFlagsVertical = SizeFlags.ShrinkEnd;
			cardInstance.CardClicked += OnHandCardClicked;
			cardInstance.CardDropped += OnHandCardDropped;
		}

		// ENEMY HAND
		foreach (var b in state.EnemyHand) {
			var cardInstance = CardScene.Instantiate<Card>();
			_enemyHandContainer.AddChild(cardInstance);
			cardInstance.CustomMinimumSize = new Vector2(117, 162);
			cardInstance.SetCardBack(b);
		}

		// CARDS ON TABLE
		foreach (var c in state.Row)
		{
			AddRowCard(c);
		}
	}

	private void ClearContainer(Node container) {
		foreach (Node card in container.GetChildren()) 
		{
			RemoveCardNode(container, card);
		}
	}
}
