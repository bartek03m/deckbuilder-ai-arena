# Format kart i talii

## Definicja karty (`data/cards.json`)

Rodzaj karty, jeden wpis na rodzaj:

```json
{
  "cards": [
    { "id": "cios", "name": "Cios", "colors": ["red"], "cost": 1, "effects": { "damage": 5 }, "rarity": "starter" }
  ]
}
```

| Pole | Typ | Opis |
|---|---|---|
| `id` | tekst | krótka nazwa bez polskich znaków, unikalna; używana w taliach i w kodzie |
| `name` | tekst | nazwa wyświetlana w grze |
| `colors` | lista | 1 albo 2 kolory z: `red`, `green`, `blue`, `purple`; dwa = karta dwukolorowa; `purple` (Joker) zawsze sam |
| `cost` | liczba | 0, 1 albo 2 |
| `effects` | obiekt | tylko `damage`, `shield`, `draw`; brak efektu = 0 |
| `rarity` | tekst | `starter`, `common`, `uncommon`, `rare` |

Przykłady na przyszłe sprinty:

```json
{ "id": "przemyslany_cios", "name": "Przemyślany cios", "colors": ["red", "blue"], "cost": 2, "effects": { "damage": 5, "draw": 1 }, "rarity": "uncommon" }
{ "id": "joker", "name": "Joker", "colors": ["purple"], "cost": 2, "effects": { "damage": 4, "shield": 4, "draw": 1 }, "rarity": "rare" }
```

## Talia (`data/decks/<id>.json`)

Lista egzemplarzy. Wypustki należą do egzemplarza, nie do definicji.

```json
{
  "id": "starter",
  "cards": [
    { "card": "cios", "count": 1, "tabs": [ { "color": "green", "value": 2 } ] },
    { "card": "cios", "count": 3 }
  ]
}
```

| Pole | Opis |
|---|---|
| `card` | `id` definicji z `cards.json` |
| `count` | ile takich egzemplarzy; brak = 1 |
| `tabs` | wypustki egzemplarza; brak = bez wypustek |
| `tabs[].color` | `red`, `green`, `blue` albo `rainbow` (tylko Joker) |
| `tabs[].value` | wartość bonusu, liczba ≥ 0 |

## Reguły, które powinna sprawdzać walidacja
- karta: 1–2 różne kolory, `purple` bez drugiego koloru, koszt 0–2, efekty ≥ 0, znana rzadkość, unikalne `id`,
- egzemplarz: najwyżej 2 wypustki, różne kolory wypustek, `rainbow` tylko u Jokera, Joker ma dokładnie jedną wypustkę `rainbow`,
- talia: znane `id` kart, najwyżej 1 Joker.

## uid
`uid` nie występuje w JSON-ie. Nadaje go stan gry przy starcie walki, żeby dwie identyczne karty w ręce były rozróżnialne.