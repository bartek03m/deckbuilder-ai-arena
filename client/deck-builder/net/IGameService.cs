using System;
using System.Threading.Tasks;
using Salon.Proto;

public interface IGameService : IDisposable
{
    Task<RunState> StartRunAsync(long seed);
    Task<TurnResult> PlayCardAsync(string sessionId, int cardUid, bool connect = false, Color tabColor = Color.Unspecified);
    Task<TurnResult> EndTurnAsync(string sessionId);
}