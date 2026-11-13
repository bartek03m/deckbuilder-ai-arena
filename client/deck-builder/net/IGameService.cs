using System;
using System.Threading.Tasks;
using Salon.Proto;

public interface IGameService : IDisposable
{
    Task<RunState> StartRunAsync(long seed);
    Task<TurnResult> PlayCardAsync(string sessionId, int cardUid);
    Task<TurnResult> EndTurnAsync(string sessionId);
}