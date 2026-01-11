# Asyncua Cover - Dokumentacja Konfiguracji Rolet

## Spis Treści
1. [Wprowadzenie](#wprowadzenie)
2. [Wymagania](#wymagania)
3. [Parametry Konfiguracji](#parametry-konfiguracji)
4. [Przykłady Ustawień](#przykłady-ustawień)
5. [Service Calls](#service-calls)
6. [Zasady Działania](#zasady-działania)
7. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

---

## Wprowadzenie

Moduł Cover dla integracji Asyncua umożliwia sterowanie roletami, żaluzjami i innymi mechanizmami przesuwanymi za pośrednictwem protokołu OPC-UA. Pozycja roletki jest obliczana na podstawie czasu jazdy (time-based positioning), co pozwala na dokładne śledzenie pozycji bez potrzeby czujników pozycji (opcjonalnie można je dodać).

**Kluczowe cechy:**
- ⏱️ Obliczanie pozycji na podstawie czasu
- 📍 Automatyczne czujniki końcowe (fully open/closed)
- 🎮 Sterowanie open/close/stop/set_position
- 💾 Zapamiętywanie pozycji między restartami
- 🔄 Płynne aktualizacje pozycji co 100ms

---

## Wymagania

### 1. Skonfigurowany Hub Asyncua
Przed dodaniem cover'ów musisz mieć skonfigurowany Hub OPCUA. Przykład:

```yaml
asyncua:
  - name: my_opcua_hub
    url: "opc.tcp://192.168.1.100:4840"
    username: "user"
    password: "password"
    scan_interval: 30
```

### 2. Node'y OPCUA na Sterowniku
Na sterowniku muszą być dostępne następujące node'y:
- **open_nodeid** - polecenie otwarcia (przyjmuje True/False)
- **close_nodeid** - polecenie zamknięcia (przyjmuje True/False)
- **stop_nodeid** (opcjonalny) - polecenie stopu (przyjmuje True/False)
- **fully_open_nodeid** (opcjonalny) - sygnał osiągnięcia pełnego otwarcia (zwraca True/False)
- **fully_closed_nodeid** (opcjonalny) - sygnał osiągnięcia pełnego zamknięcia (zwraca True/False)

---

## Parametry Konfiguracji

### Wymagane Parametry

| Parameter | Typ | Opis |
|-----------|-----|------|
| `hub` | string | Nazwa hub'a OPCUA (musi się zgadzać z `name` w sekcji asyncua) |
| `name` | string | Nazwa roletki (wyświetlana w UI Home Assistant) |
| `nodeid` | string | Unikalny identyfikator node'a roletki w OPCUA (np. `ns=2;s=Cover1`) |
| `open_nodeid` | string | NODEID polecenia otwarcia (zapisuje True/False) |
| `close_nodeid` | string | NODEID polecenia zamknięcia (zapisuje True/False) |
| `travelling_time_down` | integer | Czas całkowitego zamknięcia w sekundach (liczba > 0) |
| `travelling_time_up` | integer | Czas całkowitego otwarcia w sekundach (liczba > 0) |

### Opcjonalne Parametry

| Parameter | Typ | Domyślnie | Opis |
|-----------|-----|----------|------|
| `unique_id` | string | auto-generated | Unikalny identyfikator entity'a (zalecane) |
| `stop_nodeid` | string | - | NODEID polecenia stopu (wysyła True/False) |
| `fully_open_nodeid` | string | - | NODEID czujnika pełnego otwarcia (czyta True/False) |
| `fully_closed_nodeid` | string | - | NODEID czujnika pełnego zamknięcia (czyta True/False) |

### Opis Parametrów

#### `travelling_time_down` / `travelling_time_up`

Określa czas w sekundach potrzebny do pełnego przejazdu roletki:

```
travelling_time_down: 30    # Zamknięcie: 0% → 100% zajmuje 30 sekund
travelling_time_up: 35      # Otwarcie: 100% → 0% zajmuje 35 sekund
```

**Dla pozycji pośrednich:**
- Chcesz otworzyć na 50% gdy `travelling_time_up=30`
- Pozycja zmienia się: 0% → 50% zajmuje ~15 sekund

**Wyliczanie czasu dla pozycji pośredniej:**
```
czas = travelling_time * (pozycja_końcowa - pozycja_początkowa) / 100
```

#### `open_nodeid` / `close_nodeid` / `stop_nodeid`

Node'y sterujące ruchem roletki:

```yaml
open_nodeid: "ns=2;s=MotorOpen"       # Otwiera roletę
close_nodeid: "ns=2;s=MotorClose"     # Zamyka roletę
stop_nodeid: "ns=2;s=MotorStop"       # Zatrzymuje ruch (opcjonalnie)
```

**Sposób działania:**
```
Otwieranie:
  1. set_value(open_nodeid, True)  → Sterownik zaczyna otwierać
  2. [Auto-updater śledzi pozycję co 100ms]
  3. Pozycja osiągnięta → set_value(open_nodeid, False)

Zatrzymanie między:
  1. set_value(open_nodeid, False) → Wyłącz otwarcie
  2. (opcjonalnie) set_value(stop_nodeid, True) → Dodatkowy sygnał stopu
```

#### `fully_open_nodeid` / `fully_closed_nodeid`

Opcjonalne czujniki końcowe:

```yaml
fully_open_nodeid: "ns=2;s=Switch_Open"     # Czujnik: roletka całkowicie otwarta (True/False)
fully_closed_nodeid: "ns=2;s=Switch_Closed" # Czujnik: roletka całkowicie zamknięta (True/False)
```

**Działanie:**
- Auto-updater czyta wartość czujnika co 100ms
- Gdy czujnik zwróci True, pozycja jest natychmiast ustawiana na 100% (open) lub 0% (closed)
- Roletka jest zatrzymywana
- **Zaleta:** Pozycja jest zawsze dokładna, nawet po restartach HA

#### `unique_id`

Unikalny identyfikator entity'a:

```yaml
unique_id: "cover_living_room_blind"
```

**Zalecenia:**
- Powinien być unikalny w obrębie całego Home Assistant
- Powinien być stabilny (nie zmieniać się między restartami)
- Pozwala na migrację entity'a bez utraty historii

---

## Przykłady Ustawień

### Przykład 1: Prosta Roletka (Bez Czujników)

Базowy setup z czasowym obliczaniem pozycji:

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Roleta Salonu"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=living_room_cover"
        travelling_time_down: 30
        travelling_time_up: 30
        open_nodeid: "ns=2;s=Cover_Open"
        close_nodeid: "ns=2;s=Cover_Close"
        unique_id: "cover_living_room"
```

**Zachowanie:**
- Całkowite otwarcie/zamknięcie: 30 sekund
- Pozycja obliczana na podstawie czasu
- Przy restartcie HA: używa ostatnio zapamiętanej pozycji

---

### Przykład 2: Roletka ze Czujnikami Końcowymi

Z czujnikami potwierdzającymi pozycję krańcową:

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Żaluzja Sypialnia"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=bedroom_blind"
        travelling_time_down: 25
        travelling_time_up: 28
        open_nodeid: "ns=2;s=Blind_Motor_Open"
        close_nodeid: "ns=2;s=Blind_Motor_Close"
        stop_nodeid: "ns=2;s=Blind_Motor_Stop"
        fully_open_nodeid: "ns=2;s=Blind_Switch_Open"
        fully_closed_nodeid: "ns=2;s=Blind_Switch_Closed"
        unique_id: "cover_bedroom_blind"
```

**Zachowanie:**
- Automatyczne synchronizowanie z czujnikami
- Gdy czujnik otwarcia = True, pozycja natychmiast → 100%
- Gdy czujnik zamknięcia = True, pozycja natychmiast → 0%
- Bardzo niezawodne, nawet z różnymi czasami jazdy

---

### Przykład 3: Wiele Rolet na Jednym Hub'ie

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Saloon - Lewo"
        hub: "office_hub"
        nodeid: "ns=2;s=office_cover_left"
        travelling_time_down: 32
        travelling_time_up: 32
        open_nodeid: "ns=2;s=office_left_open"
        close_nodeid: "ns=2;s=office_left_close"
        fully_open_nodeid: "ns=2;s=office_left_open_sensor"
        fully_closed_nodeid: "ns=2;s=office_left_closed_sensor"
        unique_id: "cover_office_left"

      - name: "Saloon - Prawo"
        hub: "office_hub"
        nodeid: "ns=2;s=office_cover_right"
        travelling_time_down: 32
        travelling_time_up: 32
        open_nodeid: "ns=2;s=office_right_open"
        close_nodeid: "ns=2;s=office_right_close"
        fully_open_nodeid: "ns=2;s=office_right_open_sensor"
        fully_closed_nodeid: "ns=2;s=office_right_closed_sensor"
        unique_id: "cover_office_right"

      - name: "Okno Drzwi"
        hub: "office_hub"
        nodeid: "ns=2;s=office_door_blind"
        travelling_time_down: 20
        travelling_time_up: 20
        open_nodeid: "ns=2;s=door_open"
        close_nodeid: "ns=2;s=door_close"
        unique_id: "cover_office_door"
```

---

### Przykład 4: Roletka z Asymetrycznym Czasem

Roletka, która szybciej się otwiera niż zamyka:

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Heavy Roller Shutter"
        hub: "building_hub"
        nodeid: "ns=2;s=heavy_shutter"
        travelling_time_down: 45    # Zamykanie trwa dłużej (ciężkie)
        travelling_time_up: 25      # Otwieranie szybsze (sprężyny)
        open_nodeid: "ns=2;s=shutter_open"
        close_nodeid: "ns=2;s=shutter_close"
        stop_nodeid: "ns=2;s=shutter_stop"
        unique_id: "cover_heavy_shutter"
```

**Konsekwencje:**
```
Pozycja 50%:
  - Od 0% do 50%: jeśli zamyka → 22.5 sekund
  - Od 100% do 50%: jeśli otwiera → 12.5 sekund
```

---

## Service Calls

### `cover.open_cover`

Całkowicie otwiera roletę:

```yaml
service: cover.open_cover
target:
  entity_id: cover.roletka_salonu
```

---

### `cover.close_cover`

Całkowicie zamyka roletę:

```yaml
service: cover.close_cover
target:
  entity_id: cover.roletka_salonu
```

---

### `cover.stop_cover`

Zatrzymuje roletę w bieżącej pozycji:

```yaml
service: cover.stop_cover
target:
  entity_id: cover.roletka_salonu
```

---

### `cover.set_cover_position`

Przesuwa roletę do określonej pozycji (0-100):

```yaml
service: cover.set_cover_position
target:
  entity_id: cover.roletka_salonu
data:
  position: 50  # 0 = zamknięta, 100 = otwarta
```

**Przykład:** Roletę na 30% (bardzo zamknięta):
```yaml
service: cover.set_cover_position
target:
  entity_id: cover.roletka_salonu
data:
  position: 30
```

---

### `asyncua_cover.reset_fully_open`

Resetuje pozycję na 100% (całkowicie otwarta) - użyteczne po ręcznym otwarciu:

```yaml
service: asyncua_cover.reset_fully_open
target:
  entity_id: cover.roletka_salonu
```

---

### `asyncua_cover.reset_fully_closed`

Resetuje pozycję na 0% (całkowicie zamknięta) - użyteczne po ręcznym zamknięciu:

```yaml
service: asyncua_cover.reset_fully_closed
target:
  entity_id: cover.roletka_salonu
```

---

## Zasady Działania

### Algorytm Obliczania Pozycji

Roletka śledzi pozycję na podstawie czasu jazdy:

```
Bieżąca pozycja = Pozycja początkowa + (Pozycja końcowa - Pozycja początkowa) × (Czas upłynięty / Czas całkowity)
```

**Przykład:**
```
travelling_time_up: 30s
Otwarcie: 0% → 100%

Po 10 sekundach:
  pozycja = 0 + (100 - 0) × (10 / 30) = 33%

Po 20 sekundach:
  pozycja = 0 + (100 - 0) × (20 / 30) = 67%

Po 30 sekundach:
  pozycja = 100% (osiągnięta)
```

---

### Cykl Sterowania

```
1. Polecenie (np. set_position(60))
   ↓
2. Sprawdzenie kierunku:
   - Pozycja bieżąca: 40%
   - Pozycja docelowa: 60%
   - Kierunek: UP (otwarcie)
   ↓
3. Wysłanie sygnału START:
   - set_value(open_nodeid, True)
   - Start auto-updater (co 100ms)
   ↓
4. Auto-updater śledzi:
   - Czyta czujniki (jeśli są)
   - Aktualizuje pozycję
   - Aktualizuje UI Home Assistant
   ↓
5. Sprawdzenie pozycji osiągniętej:
   - Pozycja == 60%? → TAK
   ↓
6. Wysłanie sygnału STOP:
   - set_value(open_nodeid, False)
   - (opcjonalnie) set_value(stop_nodeid, True)
   - Stop auto-updater
   ↓
7. Roletka zatrzymana na 60%
```

---

### Integracja Czujników

Jeśli `fully_open_nodeid` lub `fully_closed_nodeid` są skonfigurowane:

```
Auto-updater (co 100ms):
  ├─ Czytaj fully_open_nodeid
  │  └─ Jeśli True → set_position(100), stop_cover()
  ├─ Czytaj fully_closed_nodeid
  │  └─ Jeśli True → set_position(0), stop_cover()
  └─ Aktualizuj UI
```

**Korzyści:**
- Pozycja zawsze dokładna, nawet jeśli HA restartnie
- Automatyczna synchronizacja z rzeczywistym sterownikiem
- Tolerancja na różne czasy jazdy

---

## Rozwiązywanie Problemów

### Problem: Roletka nie reaguje na polecenia

**Diagnoza:**
1. Sprawdź czy hub OPCUA jest dostępny:
   ```yaml
   asyncua:
     - name: my_hub
       url: "opc.tcp://IP:PORT"
   ```

2. Sprawdź czy node'y OPCUA istnieją na sterowniku:
   - `open_nodeid` musi być dostępny
   - `close_nodeid` musi być dostępny

3. Sprawdź logi Home Assistant:
   ```
   Logger: asyncua
   Szukaj: "Error sending command"
   ```

**Rozwiązanie:**
- Potwierdzić dostęp do OPCUA (test ping do IP)
- Potwierdzić NODEID'y (użyć OPC-UA Explorer)
- Sprawdzić username/hasło w hub'ie

---

### Problem: Pozycja się nie zmienia lub zmienia się powoli

**Diagnoza:**
1. Roletka jest w ruchu? → sprawdzić w UI (is_opening / is_closing)
2. Czy traveling_time są prawidłowe?

**Rozwiązanie:**
- Zmierzyć rzeczywisty czas od 0% do 100%
- Zaktualizować `travelling_time_down` i `travelling_time_up`

```yaml
# Zmierz rzeczywisty czas
# Jeśli rzeczywisty: 35 sekund
travelling_time_down: 35
```

---

### Problem: Roletka zatrzymuje się w połowie drogi

**Diagnoza:**
1. Czy `stop_nodeid` jest skonfigurowany?
2. Czy sterownik wymaga sygnału STOP między komendami?

**Rozwiązanie:**
```yaml
# Dodaj stop_nodeid
stop_nodeid: "ns=2;s=Motor_Stop"
```

---

### Problem: Czujniki nie działają

**Diagnoza:**
1. Czy czujniki zawracają True/False?
2. Czy NODEID'y czujników są prawidłowe?

**Sprawdzenie:**
```python
# W REST API sprawdź stan node'a
GET /api/states/sensor.asyncua_fully_open
# Powinien zwracać True lub False
```

**Rozwiązanie:**
- Sprawdzić czy czujniki są faktycznie podłączone
- Sprawdzić czy zwracają prawidłowe wartości logiczne
- Ewentualnie tymczasowo usunąć czujniki i konfigurować bez nich

---

### Problem: Pozycja się resetuje po restarcie

**Przyczyna:**
- Brak `fully_open_nodeid` / `fully_closed_nodeid`
- Roletka zostaje przesunięta fizycznie

**Rozwiązanie:**
- Dodaj czujniki końcowe (najlepszy wariant)
- LUB: Ręcznie resetuj pozycję:
  ```yaml
  automation:
    - trigger:
        platform: homeassistant
        event: start
      action:
        service: asyncua_cover.reset_fully_closed
        target:
          entity_id: cover.roletka
  ```

---

## Notatki

- **Dokładność pozycji:** ±1% (zaokrąglenie do liczb całkowitych)
- **Częstość aktualizacji:** co 100 milisekund
- **Stan:** `assumed_state: True` (obliczona pozycja, nie rzeczywista)
- **Zapamiętywanie:** Pozycja zapisywana jest między restartami HA

---

**Wersja dokumentacji:** 1.0  
**Data:** 2026-01-11  
**Kompatybilność:** Asyncua v0.1.2+
