# MCTS - Monte Carlo Tree Search

Algorytm do wybierania najlepszego ruchu w grze. Zamiast przeszukiwać całe drzewo gry, MCTS uruchamia tysiące szybkich symulacji i buduje statystykę, które ruchy najczęściej prowadzą do wygranej.
Pętla uruchamiana tysiące razy:

1. **Selekcja** – od korzenia schodzimy w dół, w każdym węźle wybierając dziecko z najwyższym UCT.
2. **Rozwinięcie** – dodajemy do drzewa jeden nowy węzeł (niesprawdzony ruch).
3. **Symulacja** – od nowego węzła gramy losowo do końca gry; tych ruchów nie zapisujemy.
4. **Propagacja wsteczna** – wynik dopisujemy do wszystkich węzłów na ścieżce do korzenia.

## Wartości w węźle

- **N (odwiedziny)** – ile iteracji przeszło przez węzeł.
- **W (punkty)** – suma wyników tych symulacji (wygrana 1, remis 0,5, przegrana 0), z perspektywy gracza, który wykonał ruch do tego węzła.

UCT = W/N + c · √(ln N_rodzica / N), c ≈ 1,41. Nieodwiedzony węzeł (N = 0) ma UCT = ∞.

**Decyzja** = ruch z korzenia z największym N.


## ISMCTS - Information Set MCTS

Ten sam algorytm, ale dla gier z ukrytą informacją. MCTS wymaga znajomości całego stanu gry, a my nie znamy kart w ręce przeciwnika ani kolejności talii. ISMCTS przeszukuje **zbiór informacyjny**, czyli wszystkie stany zgodne z tym, co widzimy (np. wszystkie ręce przeciwnika pasujące do jego rewersów (card back)).

Różnice względem MCTS:

0. **Losowanie (determinizacja)** – na początku *każdej* iteracji losujemy ukryte karty: rękę przeciwnika z jego talii, zgodną z kolorami rewersów, i kolejność obu talii. Całą iterację gramy na tym wylosowanym stanie.
1. **Selekcja** – bierzemy pod uwagę tylko ruchy możliwe w wylosowanym stanie; niemożliwe pomijamy.
2. **Rozwinięcie** – bez zmian (nowy węzeł spośród możliwych ruchów).
3. **Symulacja** – gramy losowo na wylosowanym stanie, a nie na prawdziwym, bo prawdziwego nie znamy.
4. **Propagacja wsteczna** – bez zmian.

**Jedno drzewo** dla wszystkich iteracji. Statystyki z różnych wylosowanych rąk sumują się w tych samych węzłach, więc ruch jest oceniany średnio po wszystkich możliwych rękach przeciwnika.

**Licznik dostępności (dost.)** – w ilu iteracjach ruch był możliwy. W UCT zastępuje N_rodzica:

UCT = W/N + c · √(ln dost. / N)


## Zastosowanie w Salonie Automatów

### Gdzie użyjemy ISMCTS
- **Lustro (Mirror) (F30, boss stołu 5):** ISMCTS v0 w S4-08, pełna wersja w S5-06.
- **Podpowiedź (hint) (F36, S7-06):** ten sam algorytm, tylko liczony z obserwacji gracza; `GetHint` zwraca ruch z największym N.
- **„Myśli automatu” (Automaton Thoughts) (F37):** rozważane ruchy i ich oceny to po prostu dzieci korzenia z ich N i W/N.
- **Poziomy trudności (F33):** liczba iteracji albo limit czasu (1–2 s na ruch).
- **Model gracza (F31, S7-04):** w symulacjach ruchy gracza wybiera model jego stylu zamiast losowania.

### Co jest ukryte (to losujemy w determinizacji)
- karty w ręce przeciwnika: znamy ich **kolory** (`opponent_hand`) i całą jego talię (`opponent_deck_list`), więc losujemy tylko spośród kart w pasujących kolorach,
- kolejność obu talii, czyli co kto dobierze,
- odwrócenie Jokera (Joker backfire): zdarzenie losowe, rozstrzygane w symulacji przez `random.Random(seed)`.

### Jak to pasuje do interfejsu automatu
- Lustro (Mirror) to zwykły automat: `choose_action(obs, legal)`.
- Nie oszukuje: nie dostaje stanu gry, tylko z `Observation` buduje **wymyślony** stan zgodny z tym, co widzi.
- Każda iteracja = nowa determinizacja → selekcja → rozwinięcie → symulacja → propagacja wsteczna.

### Specyfika naszej gry
- Tura to kilka `PlayCard` i na końcu `EndTurn`, więc w drzewie jeden ruch to jedna karta, a pod ruchem gracza często jest kolejny ruch tego samego gracza.
- Dobieranie (draw) jest dopiero po „Atak!” (ATTACK!), więc ułożenie własnego rzędu (row) nie zależy od ukrytych kart. Ukryta informacja ma znaczenie dopiero przy odpowiedzi przeciwnika (np. czy stawiać Tarczę (Shield) na jego czerwone rewersy (card back)). Na tym Lustro (Mirror) ma wygrywać z Młotem (Hammer), który planuje tylko własną turę.
- Wylosowanym kartom przeciwnika trzeba nadać nowe `uid` (`uid` nadaje stan gry, nie JSON).

### Czego ISMCTS potrzebuje od silnika (F09, S2-01)
- `legal_actions(state)` i `apply(state, action)` jako czyste funkcje,
- szybkie kopiowanie stanu, bo od tego zależy liczba iteracji w 1–2 s (pomiar w S3-07),
- funkcji budującej stan gry z `Observation` i wylosowanych kart (propozycja nazwy: `state_from_observation`).

### Co daje `Observation` (S2-07, DAA-89)
- **Stos odrzuconych (discard pile) przeciwnika** (`opponent_discard`): determinizacja losuje jego rękę i talię tylko spośród kart z `opponent_deck_list`, których nie ma na tym stosie.
- **Własna talia i własny stos odrzuconych** (`deck_list`, `discard`): to, co sami możemy dobrać, to `deck_list` bez ręki, rzędu (row) i `discard`.
- **Rząd przeciwnika jest ukryty, dopóki ten nie kliknie „Atak!” (ATTACK!).** Potem jego karty leżą na stosie odrzuconych. Lustro (Mirror) decyduje tylko w swojej turze, a wtedy rząd przeciwnika jest pusty, więc to mu nie przeszkadza.

### Prototyp z DAA-77
- Ogólny MCTS za protokołem `GameState` (`legal_moves` / `play` / `is_terminal` / `reward` / `player_to_move`), sprawdzony na kółku i krzyżyku. Silnik Salonu będzie miał funkcje `legal_actions` / `apply`, więc w S4-08 wystarczy cienki adapter.
- W S4-08 podmieniamy tylko grę na silnik Salonu i dodajemy determinizację oraz licznik dostępności.