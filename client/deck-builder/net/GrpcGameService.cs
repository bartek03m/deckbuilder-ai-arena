using System;
using System.Threading.Tasks;
using Grpc.Net.Client;
using Salon.Proto;

public sealed class GrpcGameService : IGameService
{
	private static readonly TimeSpan CallTimeout = TimeSpan.FromSeconds(3);

	private readonly GrpcChannel _channel;
	private readonly Game.GameClient _client;

	public GrpcGameService(string address)
	{
		_channel = GrpcChannel.ForAddress(address);
		_client = new Game.GameClient(_channel);
	}

	public Task<RunState> StartRunAsync(long seed) =>
		_client.StartRunAsync(new StartRunRequest { Seed = seed }, deadline: Deadline()).ResponseAsync;

	public Task<TurnResult> PlayCardAsync(string sessionId, int cardUid) =>
		_client.PlayCardAsync(new PlayCardRequest { SessionId = sessionId, CardUid = cardUid }, deadline: Deadline()).ResponseAsync;

	public Task<TurnResult> EndTurnAsync(string sessionId) =>
		_client.EndTurnAsync(new EndTurnRequest { SessionId = sessionId }, deadline: Deadline()).ResponseAsync;

	public void Dispose() => _channel.Dispose();

	private static DateTime Deadline() => DateTime.UtcNow.Add(CallTimeout);
}