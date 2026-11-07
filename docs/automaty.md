# Interfejs automatu

Kod: `server/salon/automata/interface.py`

Każdy automat ma:
- `name: str`
- `choose_action(obs: Observation, legal: list[Action]) -> Action`

`Observation` zawiera tylko to, co widzi dana strona:
- własne HP, Tarczę, energię, liczbę kart w talii i na stosie odrzuconych,
- to samo dla przeciwnika,
- własną rękę i rząd w całości,
- rękę przeciwnika tylko jako kolory rewersów,
- jawną listę talii przeciwnika,
- numer rundy.

`Action` to `PlayCard(card_uid, connect=True, tab_color=None)` albo `EndTurn()` (przycisk „Atak!”).

Zasady:
1. Automat zwraca ruch z listy `legal`. Dozwolone ruchy liczy silnik, nie automat.
2. Automat nie ma dostępu do stanu gry, tylko do `Observation`. Testy to sprawdzają (S2-08).
3. Losowość automatu korzysta z własnego `random.Random(seed)`, żeby walki dało się odtworzyć.
4. Interfejs nie zależy od gRPC; automaty nie importują `salon_proto`.