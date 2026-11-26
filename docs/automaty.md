# Interfejs automatu

Kod: `server/salon/automata/interface.py`

Każdy automat ma:
- `name: str`
- `choose_action(obs: Observation, legal: list[Action]) -> Action`

`Observation` zawiera tylko to, co widzi dana strona:
- własne HP, Tarczę (Shield), energię, liczbę kart w talii i na stosie odrzuconych (discard pile),
- to samo dla przeciwnika,
- własną rękę i rząd (row) w całości,
- listę całej własnej talii (`deck_list`),
- własny stos odrzuconych (discard pile, `discard`),
- rękę przeciwnika tylko jako kolory rewersów (card back),
- listę całej talii przeciwnika (`opponent_deck_list`),
- stos odrzuconych przeciwnika (`opponent_discard`),
- numer rundy.

Listy talii (`deck_list`, `opponent_deck_list`) to wszystkie karty danej strony w tej walce, bez względu na to, gdzie leżą, i nie zmieniają się w trakcie walki. Listy talii i stosy odrzuconych są posortowane po `uid`, więc ich kolejność nic nie zdradza. Ręka i rząd zostają w zwykłej kolejności. Rząd (row) widzi tylko strona, która ma turę. Obserwację buduje `observe(state, for_player)` w `server/salon/engine/observation.py`.

`Action` to `PlayCard(card_uid, connect=True, tab_color=None)` albo `EndTurn()` (przycisk „Atak!” (ATTACK!)).

Zasady:
1. Automat zwraca ruch z listy `legal`. Dozwolone ruchy liczy silnik, nie automat.
2. Automat nie ma dostępu do stanu gry, tylko do `Observation`. Testy to sprawdzają (S2-08).
3. Losowość automatu korzysta z własnego `random.Random(seed)`, żeby walki dało się odtworzyć.
4. Interfejs nie zależy od gRPC; automaty nie importują `salon_proto`.