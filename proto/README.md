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