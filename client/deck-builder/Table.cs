using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using Salon.Proto;
using ProtoCard = Salon.Proto.Card;
using ProtoSide = Salon.Proto.Side;

public partial class Table : Control
{
	// CARD SCENE
	[Export] public PackedScene CardScene { get; set; }

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

		_playerHandContainer = GetNode<HBoxContainer>("BottomBar/PlayerHand");
		_enemyHandContainer  = GetNode<HBoxContainer>("TopBar/EnemyHand");
		_rowContainer        = GetNode<HBoxContainer>("MiddleArea/RowContainer");

		// MOCK SERVICE
		var mockService = new MockGameService();
		var run = await mockService.StartRunAsync(42);
		UpdateState(run.Battle);
	}

	// UPDATE STATE
	public void UpdateState(BattleState state)
	{
		if (state == null) return;

		UpdateStats(state);
		UpdateCards(state);
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
		}

		// ENEMY HAND
		foreach (var b in state.EnemyHand) {
			var cardInstance = CardScene.Instantiate<Card>();
			_enemyHandContainer.AddChild(cardInstance);
			cardInstance.CustomMinimumSize = new Vector2(117, 162);
			cardInstance.SetCardBack(b);
		}

		// CARDS ON TABLE
		foreach (var c in state.Row) {
			var cardInstance = CardScene.Instantiate<Card>();
			_rowContainer.AddChild(cardInstance);
			cardInstance.SetCardData(c);
		}
	}

	private void ClearContainer(Node container) {
		foreach (Node card in container.GetChildren()) 
		{
			card.QueueFree();
		}
	}
}
