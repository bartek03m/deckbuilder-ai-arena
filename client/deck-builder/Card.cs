using Godot;
using System;

public partial class Card : ColorRect
{
	bool isDragging = false; // czy gracz aktualnie trzyma karte
	Vector2 dragOffset; // zapamiętuje współrzędne karty (środek karty to x,y)

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta){
		if (isDragging == true){
			GlobalPosition = GetGlobalMousePosition() - dragOffset;
		}
	}
	
	public override void _GuiInput(InputEvent @event){
		if (@event is InputEventMouseButton mouseEvent){ // jeśli event był kliknięciem myszki to przypisujemy do zmiennej mouseEvent
			if (mouseEvent.ButtonIndex == MouseButton.Left) {
				if (mouseEvent.Pressed) {
					isDragging = true;
					dragOffset = GetGlobalMousePosition() - GlobalPosition;
				}
				else {
					isDragging = false;
				}
			}
		} 
	}
}
