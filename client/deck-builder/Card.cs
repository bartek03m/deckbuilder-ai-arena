using Godot;
using System.Collections.Generic;
using System.Linq;
using ProtoCard  = Salon.Proto.Card;
using ProtoColor = Salon.Proto.Color;
using ProtoTab   = Salon.Proto.Tab;

public partial class Card : ColorRect
{
	// SIGNAL
	[Signal] public delegate void CardClickedEventHandler(int cardUid);
	[Signal] public delegate void CardDroppedEventHandler(int cardUid, Vector2 globalPosition);

	// EXPORT
	[Export] public Vector2 TabSize { get; set; } = new(24, 20);

	// REFERENCES
	private Label _costLabel;
	private Label _nameLabel;
	private Label _effectLabel;
	private VBoxContainer _tabsContainer;

	// CARD DATA
	private int _cardUid;
	private bool _isReverse; // true = enemy card back (shows only colors)
	private List<ProtoColor> _currentColors = new();

	// DRAG STATE
	private const float ClickDragThreshold = 5f;
	private bool _isDragging; // true = player is dragging the card
	private Vector2 _dragOffset; // offset between mouse position and card position
	private Vector2 _pressPosition; // mouse position when clicked, to distinguish click from drag

	// COLOR PALETTE	
	// CardColors — card background color
	// TabColors  — tab color
	private static readonly Dictionary<ProtoColor, Godot.Color> CardColors = new()
	{
		{ ProtoColor.Red,         new Godot.Color("b03030") }, // attack red
		{ ProtoColor.Green,       new Godot.Color("2d8a4e") }, // defense green
		{ ProtoColor.Blue,        new Godot.Color("2a6099") }, // draw blue
		{ ProtoColor.Purple,      new Godot.Color("7b3fa0") }, // joker purple
		{ ProtoColor.Unspecified, new Godot.Color("4a3828") }, // neutral brown
	};

	private static readonly Dictionary<ProtoColor, Godot.Color> TabColors = new()
	{
		{ ProtoColor.Red,     new Godot.Color("e04040") }, // red tab
		{ ProtoColor.Green,   new Godot.Color("40c060") }, // green tab
		{ ProtoColor.Blue,    new Godot.Color("4080e0") }, // blue tab
		{ ProtoColor.Rainbow, new Godot.Color("f0c020") }, // rainbow tab
	};

	public override void _Ready()
	{
		_costLabel = GetNode<Label>("CostLabel");
		_nameLabel = GetNode<Label>("NameLabel");
		_effectLabel = GetNode<Label>("EffectLabel");
		_tabsContainer = GetNode<VBoxContainer>("TabsContainer");
		_costLabel.MouseFilter = MouseFilterEnum.Ignore;
		_nameLabel.MouseFilter = MouseFilterEnum.Ignore;
		_effectLabel.MouseFilter = MouseFilterEnum.Ignore;
		_costLabel.HorizontalAlignment = HorizontalAlignment.Center;
		_costLabel.VerticalAlignment = VerticalAlignment.Center;
	}

	public override void _Process(double delta) // _Process(delta) — call every frame to move the card if _isDragging is true
	{
		if (_isDragging)
		{
			GlobalPosition = GetGlobalMousePosition() - _dragOffset;
		}
	}

	public override void _GuiInput(InputEvent @event)
	{
		if (_isReverse)
			return; // ignore all input on card backs

		if (@event is InputEventMouseButton mouseEvent &&
			mouseEvent.ButtonIndex == MouseButton.Left)
		{
			if (mouseEvent.Pressed)
			{
				_isDragging = true;
				_pressPosition = mouseEvent.GlobalPosition;
				_dragOffset = GetGlobalMousePosition() - GlobalPosition;
			}
			else if (_isDragging)
			{
				_isDragging = false;
				float distanceMoved = mouseEvent.GlobalPosition.DistanceTo(_pressPosition);
				if (distanceMoved < ClickDragThreshold)
				{
					EmitSignal(SignalName.CardClicked, _cardUid);
				}
				else
				{
					EmitSignal(SignalName.CardDropped, _cardUid, GlobalPosition);
				}
			}
		}
	}

	//PUBLIC API

	/// <summary>
	/// Populate the card visuals from a proto Card message (player's own card).
	/// </summary>

	public void SetCardData(ProtoCard data)
	{
		_cardUid   = data.Uid;
		_isReverse = false;

		// Background color – first color in the list, fallback to neutral
		_currentColors = data.Colors.ToList();
		Color = Colors.Transparent;

		// Labels
		_costLabel.Text   = data.Cost.ToString();
		_nameLabel.Text   = data.Name;
		_effectLabel.Text = FormatEffects(data);

		// Tabs
		RebuildTabs(data.Tabs);

		QueueRedraw();
		Show();
	}

	/// <summary>
	/// Show the card as an enemy reverse – only colors visible,
	/// no name / cost / effect / tabs.
	/// </summary>
	
	public void SetReverse(Salon.Proto.CardBack back)
	{
		_cardUid   = -1;
		_isReverse = true;

		_currentColors = back.Colors.ToList();
		Color = Colors.Transparent;

		_costLabel.Text   = "";
		_nameLabel.Text   = "";
		_effectLabel.Text = "";

		ClearTabs();
		QueueRedraw();
		Show();
	}

	/// <summary>
	/// Card uid from proto, used to send PlayCard requests.
	/// </summary>
	
	public int CardUid => _cardUid;

	/// <summary>
	/// Returns the background color of a card based on its base colors from the proto.
	/// 0 colors -> brown (fallback/error)
	/// 1 color -> the color directly from the palette (red)
	/// 2 colors -> a 50/50 blend of both colors (dual-colored card)
	/// </summary>
	
	public override void _Draw()
	{
		if (_currentColors.Count <= 1)
		{
			var col = _currentColors.Count == 1 
				? CardColors.GetValueOrDefault(_currentColors[0], CardColors[ProtoColor.Unspecified])
				: CardColors[ProtoColor.Unspecified];

			DrawRect(new Rect2(Vector2.Zero, Size), col);
		}
		else if (_currentColors.Count == 2)
		{
			var c1 = CardColors.GetValueOrDefault(_currentColors[0], CardColors[ProtoColor.Unspecified]);
			var c2 = CardColors.GetValueOrDefault(_currentColors[1], CardColors[ProtoColor.Unspecified]);

			Vector2 topLeft     = Vector2.Zero;
			Vector2 topRight    = new Vector2(Size.X, 0);
			Vector2 bottomRight = Size;
			Vector2 bottomLeft  = new Vector2(0, Size.Y);

			DrawPolygon(
				new Vector2[] { topLeft, topRight, bottomLeft },
				new Godot.Color[] { c1, c1, c1 }
			);

			DrawPolygon(
				new Vector2[] { topRight, bottomRight, bottomLeft },
				new Godot.Color[] { c2, c2, c2 }
			);
		}

		if (!_isReverse && _costLabel != null && !string.IsNullOrEmpty(_costLabel.Text))
		{
			Vector2 orbCenter = new Vector2(20, 18);
			DrawCircle(orbCenter, 13, new Godot.Color("f1c40f"));
			DrawArc(orbCenter, 13, 0, Mathf.Tau, 32, new Godot.Color("#575555"), 2.0f);
		}
	}

	private static string FormatEffects(ProtoCard card)
	{
		var parts = new List<string>();
		if (card.Damage > 0) parts.Add($"Damage: {card.Damage}");
		if (card.Shield > 0) parts.Add($"Shield: {card.Shield}");
		if (card.Draw   > 0) parts.Add($"Draw: {card.Draw}");
		return parts.Count > 0 ? string.Join("\n", parts) : "-";
	}

	/// <summary>
	/// Deletes old tabs from TabsContainer and creates new ones based on proto data.
	/// Each tab is a small colored rectangle (ColorRect) with a number in the middle (Label).
	/// </summary>
	 
	private void RebuildTabs(Google.Protobuf.Collections.RepeatedField<ProtoTab> tabs)
	{
		ClearTabs();
		if (tabs == null) return;

		foreach (var tab in tabs)
		{
			Control tabNode;

			if (tab.Color == ProtoColor.Rainbow)
			{
				var rainbowBase = new Control
				{
					CustomMinimumSize = TabSize,
					MouseFilter = MouseFilterEnum.Pass,
					TooltipText = $"Rainbow +{tab.Value}"
				};

				var stripes = new HBoxContainer
				{
					MouseFilter = MouseFilterEnum.Pass
				};
				stripes.SetAnchorsPreset(LayoutPreset.FullRect);
				stripes.AddThemeConstantOverride("separation", 0);

				Godot.Color[] rainbowColors = {
					TabColors[ProtoColor.Red],
					TabColors[ProtoColor.Green],
					TabColors[ProtoColor.Blue]
				};

				foreach (var color in rainbowColors)
				{
					stripes.AddChild(new ColorRect
					{
						Color = color,
						SizeFlagsHorizontal = SizeFlags.ExpandFill,
						SizeFlagsVertical = SizeFlags.ExpandFill,
						MouseFilter = MouseFilterEnum.Pass
					});
				}

				rainbowBase.AddChild(stripes);
				tabNode = rainbowBase;
			}
			else
			{
				tabNode = new ColorRect
				{
					CustomMinimumSize = TabSize,
					Color = TabColors.GetValueOrDefault(tab.Color, new Godot.Color("888888")),
					TooltipText = $"{tab.Color} +{tab.Value}",
					MouseFilter = MouseFilterEnum.Pass
				};
			}

			// Value label inside the tab
			var valueLabel = new Label
			{
				Text = $"+{tab.Value}",
				HorizontalAlignment = HorizontalAlignment.Center,
				VerticalAlignment   = VerticalAlignment.Center,
			};
			valueLabel.AddThemeColorOverride("font_color", Colors.White);
			valueLabel.AddThemeConstantOverride("outline_size", 2);
			valueLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			valueLabel.SetAnchorsPreset(LayoutPreset.FullRect);

			tabNode.AddChild(valueLabel);
			_tabsContainer.AddChild(tabNode);
		}
	}

	/// <summary>
	/// Removes all children from TabsContainer (old tabs).
	/// QueueFree() = "remove this node at the end of the current frame" - the safe way to delete in Godot.
	/// We don't use Remove/Delete because Godot manages memory - QueueFree is the standard approach here.
	/// </summary>
	private void ClearTabs()
	{
		// GetChildren() returns a list of all children of TabsContainer
		foreach (Node child in _tabsContainer.GetChildren())
			child.QueueFree();
	}
}
