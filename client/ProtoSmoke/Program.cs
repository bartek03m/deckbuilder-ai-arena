using Grpc.Core;
using Grpc.Net.Client;
using Salon.Proto;

using var channel = GrpcChannel.ForAddress("http://127.0.0.1:50051");
var client = new Game.GameClient(channel);

var run = await client.StartRunAsync(new StartRunRequest { Seed = 42 });
Console.WriteLine($"Player HP: {run.Battle.Player.Hp}");
var first = run.Battle.Hand[0];
var tab = first.Tabs.Count > 0 ? first.Tabs[0].Color.ToString() : "none";
Console.WriteLine($"First card: {first.Name}, tab {tab}");

var result = await client.PlayCardAsync(new PlayCardRequest { SessionId = run.SessionId, CardUid = first.Uid });
foreach (var e in result.Events)
{
    switch (e.KindCase)
    {
        case Event.KindOneofCase.CardPlayed:
            Console.WriteLine($"Event: played {e.CardPlayed.Card.Name}");
            break;
        default:
            Console.WriteLine($"Event: {e.KindCase}");
            break;
    }
}
Console.WriteLine($"Energy: {result.State.Player.Energy}, in row: {result.State.Row.Count}");

try
{
    await client.EndTurnAsync(new EndTurnRequest { SessionId = run.SessionId });
}
catch (RpcException ex)
{
    Console.WriteLine($"EndTurn: {ex.StatusCode}");
}