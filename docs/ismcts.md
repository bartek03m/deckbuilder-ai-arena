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

## ISMCTS

TODO

## Zastosowanie w Salonie Automatów

TODO