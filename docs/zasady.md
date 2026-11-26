# Salon Automatów - zasady walki

## 1. Cel gry

Walka to pojedynek 1 na 1 między graczem a automatem. Wygrywa strona, która pierwsza zbije przeciwnikowi HP do zera. Pierwszą turę zawsze rozpoczyna gracz.

## 2. Karty

### 2.1 Budowa karty

Każda karta składa się z czterech elementów:

| Element | Znaczenie |
|---|---|
| **Kolor** | rodzaj karty; określa też, z którymi wypustkami (tab) poprzedniej karty ta karta się łączy |
| **Koszt** | liczba punktów energii potrzebna do zagrania karty: 0, 1 albo 2. Karta połączona z poprzednią kosztuje 1 mniej |
| **Efekt główny** | działanie karty: zadanie obrażeń (damage), dodanie Tarczy (Shield) albo dobranie (draw) kart. Karty dwukolorowe (Dual-color) mają dwa efekty |
| **Wypustki** | od 0 do 2 kolorowych znaczników z liczbą na **prawej krawędzi** karty |

Przykład - karta Cios (Strike) z talii startowej (starter deck):

| Kolor | Koszt | Nazwa | Efekt główny | Wypustki |
|---|---|---|---|---|
| 🟥 | 1 | Cios | 5 obrażeń | 🟩 +2 |

Czerwona karta ataku (Strike) o koszcie 1 zadaje 5 obrażeń. Jeśli bezpośrednio po niej zostanie położona karta zielona, zagrywający otrzymuje dodatkowo +2 Tarczy.

### 2.2 Rodzaje kart

| Rodzaj | Kolor | Efekt główny | Uwagi |
|---|---|---|---|
| Atak (Attack) | 🟥 czerwony | zadaje obrażenia (damage) | - |
| Obrona (Defense) | 🟩 zielony | daje Tarczę (Shield) | Tarcza chroni przed obrażeniami |
| Dobieranie (Draw) | 🟦 niebieski | dobiera karty | karty trafiają do ręki na koniec tury |
| Dwukolorowa (Dual-color) | 🟥🟩, 🟥🟦 albo 🟩🟦 | dwa efekty naraz, np. 5 obrażeń + dobranie 1 karty | dostępna od 2. stołu kampanii (campaign) |
| Joker | 🟪 fioletowy | kilka efektów naraz | może obrócić się przeciwko zagrywającemu; maks. 1 w talii |

### 2.3 Wypustki

Wypustka (tab) to kolorowy znacznik z liczbą, np. 🟩 +2. Jej kolor określa:

1. **z jaką kartą się łączy** - następna położona karta musi mieć ten kolor,
2. **jaki bonus daje** po połączeniu (connection).

| Wypustka | Łączy się z kartą | Bonus |
|---|---|---|
| 🟥 +N | czerwoną | +N obrażeń (damage) |
| 🟩 +N | zieloną | +N Tarczy (Shield) |
| 🟦 +N | niebieską | dobranie (draw) N kart |
| 🌈 +N (tylko Joker) | dowolną | bonus w kolorze następnej karty |

- Kolor wypustki **nie zależy** od koloru karty. Karta czerwona może mieć wypustkę czerwoną, zieloną, niebieską albo nie mieć żadnej.
- Karta ma **0, 1 albo 2 wypustki**. Dwie wypustki na jednej karcie mają **zawsze różne kolory**. Joker ma zawsze jedną wypustkę tęczową.
- Karty o koszcie 0 mają najwyżej jedną wypustkę.
- Karta bez wypustek kończy ciąg (chain) połączeń.
- Wypustka działa tylko po połączeniu i nie osłabia efektu głównego karty.
- Karty zdobywane w nagrodach (reward) i w sklepie (shop) otrzymują **losowe wypustki** w chwili pojawienia się; są one widoczne przed wyborem karty. Karty talii startowej (starter deck) mają wypustki stałe.

### 2.4 Koszty kart

Koszt to liczba punktów energii, którą trzeba wydać, aby zagrać kartę. W każdej turze dostępne są 3 punkty energii. Im wyższy koszt, tym silniejszy efekt karty. Karta połączona z poprzednią kosztuje 1 punkt mniej.

| Koszt | Koszt po połączeniu (connection) | Siła karty | Przykładowy efekt karty | Liczba wypustek (tab) |
|---|---|---|---|---|
| 0 | 0 | słaba | 2 obrażenia (damage) **albo** 2 Tarczy (Shield) | 0-1 |
| 1 | 0 | średnia | 5 obrażeń **albo** 4 Tarczy **albo** dobranie (draw) 2 kart | zwykle 1, rzadko 2 |
| 2 | 1 | silna | 9 obrażeń **albo** 8 Tarczy **albo** dwa efekty naraz (karty dwukolorowe (Dual-color) i Joker) | 0-2 |

Wiersz tabeli pokazuje możliwe efekty kart o danym koszcie. Pojedyncza karta jednokolorowa ma tylko jeden z nich - np. Cios (Strike) (koszt 1) zadaje 5 obrażeń, a Blok (Block) (koszt 1) daje 4 Tarczy.

## 3. Łączenie kart

Karty zagrane w jednej turze układa się w rząd (row), od lewej do prawej. Kilka kolejno połączonych kart tworzy ciąg (chain).

- Karta **łączy się** z poprzednią, jeśli ma kolor jednej z jej wypustek (tab). Znaczenie ma tylko karta leżąca bezpośrednio po lewej.
- Połączona karta **kosztuje 1 energii mniej** (nie mniej niż 0) i **aktywuje wypustkę** poprzedniej karty.
- Aktywuje się **jedna** wypustka - ta pasująca kolorem. Jeśli pasują dwie (karta dwukolorowa (Dual-color)), zagrywający wybiera jedną; pozostałe przepadają.
- Karta dwukolorowa pasuje do wypustki w każdym ze swoich kolorów.
- Łączenie jest **nieobowiązkowe**. Każdą kartę można zagrać za pełny koszt, także rozpoczynając nowy ciąg mimo pasującej wypustki.
- W jednym rzędzie może być kilka ciągów.
- Wypustki ostatniej karty w turze przepadają. Rząd nie przechodzi na następną turę.

Przykład ciągu:

[🟥 Cios (Strike)] -🟩+2 -> [🟩 Blok (Block)] -🟥+2 -> [🟥 Cios]

Koszt: 1 + 0 + 0 = 1 energii. Wynik: 12 obrażeń (damage) (10 + 2) i 6 Tarczy (Shield) (4 + 2).

## 4. Joker 🟪

- Koszt 2, efekt: **4 obrażenia (damage) + 4 Tarczy (Shield) + dobranie (draw) 1 karty**.
- Pasuje do każdej wypustki (tab) i **aktywuje wszystkie** wypustki poprzedniej karty.
- Ma jedną **tęczową wypustkę 🌈 +3**, która pasuje do każdej następnej karty i daje bonus w jej kolorze. Przy karcie dwukolorowej (Dual-color) zagrywający wybiera kolor bonusu.
- **Odwrócenie** (Joker backfire) - przy rozliczeniu (resolution) rzędu (row), z szansą **20%**, cała kombinacja działa przeciwko zagrywającemu: on otrzymuje wszystkie obrażenia, a przeciwnik całą Tarczę i dobieranie (do limitu ręki). Odwrócenie może zakończyć walkę porażką zagrywającego.
  - Szansa maleje o 5 pkt proc. za każde połączenie (connection) przed Jokerem i rośnie o 2,5 pkt proc. za każdą kartę położoną po nim; nie spada poniżej 15%.
  - Aktualna szansa jest widoczna na karcie.
  - Tarcza z odwrócenia nie znika na początku tury przeciwnika - dolicza się do jego Tarczy.

## 5. Obrażenia, Tarcza, energia, ręka i talia

- **Tarcza** (Shield) - obrażenia (damage) najpierw zbijają Tarczę, nadwyżka trafia w HP. Tarcza nie ma limitu i znika na początku tury swojego właściciela, więc chroni w turze przeciwnika.
- **Energia** - niewykorzystana przepada.
- **Ręka** - maks. **7 kart**. Niezagrane karty zostają w ręce. Przy pełnej ręce karty nie są dobierane i zostają w talii. Samodzielne odrzucanie kart jest niedozwolone.
- **Talia** - zagrane karty trafiają na stos odrzuconych (discard pile). Gdy talia się wyczerpie, stos odrzuconych zostaje potasowany i tworzy nową talię.

## 6. Jawne rewersy

Rewers (card back) karty ma jej kolor (karta dwukolorowa (Dual-color) - oba kolory, Joker - 🟪). Każda strona widzi liczbę i kolory kart w ręce przeciwnika, ale nie ich wartości ani wypustek (tab).

Przed walką obie strony mogą przejrzeć pełną listę kart z talii przeciwnika wraz z wypustkami. Ukryte pozostaje tylko to, które karty są w ręce i w jakiej kolejności leżą w talii. Automaty podlegają tym samym zasadom.

Przykład: rewersy 🟥🟥🟥🟩 w ręce przeciwnika zapowiadają silny atak.

## 7. Przygotowanie do walki

| Parametr | Wartość |
|---|---|
| HP gracza | 50 (automaty: 30-60, zależnie od stołu) |
| Ręka początkowa | 5 kart |
| Energia | 3 na turę; w 1. turze walki strona zaczynająca ma 2 |
| Talia startowa (starter deck) | 10 kart o koszcie 1 |

### 7.1 Talia startowa gracza

Każde podejście gracz rozpoczyna z tą samą talią: 4 Ciosy (Strike), 4 Bloki (Block) i 2 Namysły (Ponder). Wypustki (tab) mają tylko 3 karty.

| Karta | Liczba kopii | Kolor | Koszt | Efekt główny | Wypustka |
|---|---|---|---|---|---|
| Cios | 1 | 🟥 | 1 | 5 obrażeń (damage) | 🟩 +2 |
| Cios | 3 | 🟥 | 1 | 5 obrażeń | brak |
| Blok | 1 | 🟩 | 1 | 4 Tarczy (Shield) | 🟥 +2 |
| Blok | 3 | 🟩 | 1 | 4 Tarczy | brak |
| Namysł | 1 | 🟦 | 1 | dobranie (draw) 2 kart | 🟥 +1 |
| Namysł | 1 | 🟦 | 1 | dobranie 2 kart | brak |

## 8. Przebieg tury

1. **Początek tury** - energia wraca do 3, Tarcza (Shield) aktywnej strony spada do 0.
2. **Wystawianie** - karty z ręki kładzie się kolejno na prawym końcu rzędu (row), płacąc ich koszt w energii. Na tym etapie karty jeszcze nie działają.
3. **Atak** - cały rząd rozlicza się jednocześnie, w kolejności:
   1. Joker - losowanie odwrócenia (Joker backfire),
   2. obrażenia (damage) (efekty główne i bonusy z wypustek (tab)),
   3. Tarcza,
   4. dobranie (draw) **3 kart** oraz wszystkich kart z efektów i bonusów dobierania.
4. **Koniec tury** - karty z rzędu trafiają na stos odrzuconych (discard pile). Turę w ten sam sposób rozgrywa przeciwnik.

## 9. Zasada przeciw patom

Od 10. rundy obie strony na początku swojej tury tracą HP: 2 w 10. rundzie, a w każdej kolejnej o 2 więcej (2, 4, 6…).

## 10. Przykładowa tura

Gracz ma 3 energii i następujące karty w ręce:

| Karta | Kolor | Koszt | Efekt główny | Wypustka (tab) |
|---|---|---|---|---|
| Cios (Strike) | 🟥 | 1 | 5 obrażeń (damage) | 🟩 +3 |
| Blok (Block) | 🟩 | 1 | 4 Tarczy (Shield) | 🟥 +3 |
| Ciężki cios (Heavy Strike) | 🟥 | 2 | 9 obrażeń | brak |
| Namysł (Ponder) | 🟦 | 1 | dobranie (draw) 2 kart | 🟥 +2 |

| Kolejność | Energia | Wynik |
|---|---|---|
| Ciężki cios -> Cios | 2 + 1 = 3 | 14 obrażeń, 0 Tarczy, dobranie 3 kart |
| Namysł -> Cios -> Blok -> Ciężki cios | 1 + 0 + 0 + 1 = 2 | 19 obrażeń, 7 Tarczy, dobranie 5 kart; 1 energii niewykorzystana |

Te same karty ułożone w innej kolejności dają inny wynik.
