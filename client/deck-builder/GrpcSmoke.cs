using System;
using Godot;
using Grpc.Core;
using Grpc.Net.Client;
using Salon.Proto;

// DAA-79 smoke test: connects to the server and shows the battle state.
public partial class GrpcSmoke : Control
{
	private const string ServerAddress = "http://127.0.0.1:50051";

	private Label _status;

	public override async void _Ready()
	{
		_status = GetNode<Label>("Status");
		_status.Text = $"Connecting to {ServerAddress}...";

		try
		{
			using var channel = GrpcChannel.ForAddress(ServerAddress);
			var client = new Game.GameClient(channel);

			var run = await client.StartRunAsync(
				new StartRunRequest { Seed = 42 },
				deadline: DateTime.UtcNow.AddSeconds(3));

			var battle = run.Battle;
			_status.Text =
				$"Connected, session: {run.SessionId}\n" +
				$"Player HP: {battle.Player.Hp}/{battle.Player.MaxHp}, energy: {battle.Player.Energy}\n" +
				$"Enemy HP: {battle.Enemy.Hp}/{battle.Enemy.MaxHp}\n" +
				$"Cards in hand: {battle.Hand.Count}";
		}
		catch (RpcException ex)
		{
			_status.Text = $"gRPC error: {ex.StatusCode}\n{ex.Status.Detail}";
		}
	}
}