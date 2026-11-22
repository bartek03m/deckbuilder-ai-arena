# Kontrakt gRPC

Plik: `salon_proto/game.proto`. Z niego generuje się kod serwera (Python) i klienta (C#).

## Generowanie kodu
- Python: `bash scripts/gen_proto.sh` (wynik w `server/salon_proto/`, nie commitujemy)
- C#: samo przy `dotnet build` (wynik w `obj/`, nie commitujemy)

## Zasady zmian
1. Nowe pole = nowy, nieużywany numer. Numerów i typów istniejących pól nie zmieniamy.
2. Pola nie kasujemy, tylko zostawiamy `reserved <numer>;`, żeby nikt nie użył numeru ponownie.
3. Każda zmiana tego pliku wymaga review od Kacpra i Oliwiera.
4. Po zmianie: wygenerować kod po obu stronach i sprawdzić, że CI przechodzi.

## Kolejność zdarzeń (v1)

Klient odtwarza `TurnResult.events` po kolei, a na końcu ustawia stół według `state`.

`PlayCard`: `CardPlayed` → `TabActivated` (jeśli połączona) → `EnergyChanged`.

`EndTurn` (przycisk „Atak!”):
1. Atak gracza: `Damage` (suma) → `ShieldChanged` → `CardsDrawn`
2. Koniec tury gracza: `CardsDiscarded`
3. Tura automatu: `ShieldChanged(0)` (jeśli > 0) → `EnergyChanged` → `CardPlayed`/`TabActivated` na każdą kartę → `Damage` → `ShieldChanged` → `CardsDrawn` → `CardsDiscarded`
4. Nowa tura gracza: `ShieldChanged(0)` (jeśli > 0) → `EnergyChanged`

Zawsze:
- `BattleEnded` jest ostatnie; po nim serwer nic nie wysyła.
- `CardPlayed` danej karty jest przed każdym zdarzeniem z jej `uid`.
- Zdarzenia tury gracza i tury automatu się nie przeplatają.