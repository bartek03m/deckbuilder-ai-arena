using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Salon.Proto;
using ProtoEvent = Salon.Proto.Event;

public sealed class EventQueue
{
	private readonly Queue<TurnResult> _pending = new();
	private readonly Func<ProtoEvent, Task> _playEvent;
	private readonly Action<BattleState> _applyState;
	private bool _running;

	public EventQueue(Func<ProtoEvent, Task> playEvent, Action<BattleState> applyState)
	{
		_playEvent = playEvent ?? throw new ArgumentNullException(nameof(playEvent));
		_applyState = applyState ?? throw new ArgumentNullException(nameof(applyState));
	}

	public bool IsBusy => _running || _pending.Count > 0;

	public event Action Idle;

	public async Task EnqueueAsync(TurnResult result)
	{
		if (result == null)
			return;
		_pending.Enqueue(result);
		if (_running)
			return;

		_running = true;
		try
		{
			while (_pending.Count > 0)
			{
				var next = _pending.Dequeue();
				foreach (var e in next.Events)
					await _playEvent(e);
				_applyState(next.State);
			}
		}
		catch
		{
			_pending.Clear();
			throw;
		}
		finally
		{
			_running = false;
		}

		Idle?.Invoke();
	}
}
