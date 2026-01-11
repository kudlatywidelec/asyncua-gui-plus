# Schemat Konfiguracji Cover - Asyncua

## Pełny Schemat YAML

```yaml
cover:
  - platform: asyncua
    nodes:
      # ROLETKA 1
      - name: "Nazwa Roletki 1"
        hub: "hub_name"
        nodeid: "ns=2;s=Cover1"
        
        # Obowiązkowe - Sterowanie
        open_nodeid: "ns=2;s=Cover1_Open"
        close_nodeid: "ns=2;s=Cover1_Close"
        
        # Obowiązkowe - Czasy
        travelling_time_down: 30
        travelling_time_up: 30
        
        # Opcjonalne - Dodatkowe sterowanie
        stop_nodeid: "ns=2;s=Cover1_Stop"
        
        # Opcjonalne - Czujniki
        fully_open_nodeid: "ns=2;s=Cover1_FullOpen"
        fully_closed_nodeid: "ns=2;s=Cover1_FullClosed"
        
        # Opcjonalne - Identyfikacja
        unique_id: "cover_room1"

      # ROLETKA 2
      - name: "Nazwa Roletki 2"
        hub: "hub_name"
        nodeid: "ns=2;s=Cover2"
        open_nodeid: "ns=2;s=Cover2_Open"
        close_nodeid: "ns=2;s=Cover2_Close"
        travelling_time_down: 25
        travelling_time_up: 28
        unique_id: "cover_room2"
```

---

## Parametry Szczegółowo

### 🔴 OBOWIĄZKOWE

#### `name`
- **Typ:** `string`
- **Opis:** Wyświetlana nazwa roletki w Home Assistant
- **Przykład:** `"Żaluzja Salon"`, `"Roleta Sypialnia"`
- **Wymagana?** ✅ TAK

#### `hub`
- **Typ:** `string`
- **Opis:** Nazwa hub'a OPCUA z sekcji `asyncua`
- **Przykład:** `"moj_hub"`, `"dom_hub"`, `"biuro_hub"`
- **Wymagana?** ✅ TAK
- **Uwaga:** Musi się zgadzać z `name` w `asyncua:`

#### `nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Unikalny identyfikator roletki w sterowniku OPCUA
- **Formaty:**
  ```
  ns=2;s=Cover1          # String identifier
  ns=2;i=1000            # Integer identifier
  ns=3;g=<UUID>          # GUID identifier
  ```
- **Wymagana?** ✅ TAK
- **Gdzie znaleźć?** OPC-UA Explorer lub dokumentacja sterownika

#### `open_nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Node do wysyłania polecenia otwarcia
- **Wartości:**
  - `True` - otwarcie
  - `False` - zatrzymanie otwarcia
- **Wymagana?** ✅ TAK
- **Przykład:** `"ns=2;s=Motor_Open"`

#### `close_nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Node do wysyłania polecenia zamknięcia
- **Wartości:**
  - `True` - zamknięcie
  - `False` - zatrzymanie zamknięcia
- **Wymagana?** ✅ TAK
- **Przykład:** `"ns=2;s=Motor_Close"`

#### `travelling_time_down`
- **Typ:** `integer`
- **Opis:** Czas całkowitego zamknięcia roletki w sekundach
- **Zakres:** > 0
- **Wymagana?** ✅ TAK
- **Jak zmierzyć?**
  1. Otwórz roletę (100%)
  2. Wyślij polecenie zamknięcia
  3. Zmierz czas do całkowitego zamknięcia
  4. Ustaw tę wartość
- **Przykład:** `30` (30 sekund)

#### `travelling_time_up`
- **Typ:** `integer`
- **Opis:** Czas całkowitego otwarcia roletki w sekundach
- **Zakres:** > 0
- **Wymagana?** ✅ TAK
- **Jak zmierzyć?**
  1. Zamknij roletę (0%)
  2. Wyślij polecenie otwarcia
  3. Zmierz czas do całkowitego otwarcia
  4. Ustaw tę wartość
- **Przykład:** `35` (35 sekund)

---

### 🟠 OPCJONALNE (ALE RACZEJ WYMAGANE)

#### `stop_nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Node do wysyłania polecenia zatrzymania
- **Wartości:**
  - `True` - wysyłane przy zatrzymaniu
  - `False` - domyślnie
- **Wymagana?** ❌ NIE (ale zalecana)
- **Kiedy potrzebna?**
  - Sterownik wymaga sygnału STOP
  - Dla pewności zatrzymania między komendami
- **Przykład:** `"ns=2;s=Motor_Stop"`

---

### 🟢 OPCJONALNE (CZUJNIKI)

#### `fully_open_nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Node czujnika osiągnięcia pełnego otwarcia
- **Czytane Wartości:**
  - `True` - roletka całkowicie otwarta
  - `False` - roletka nie jest całkowicie otwarta
- **Wymagana?** ❌ NIE (ale bardzo zalecana)
- **Korzyści:**
  - Precyzyjne potwierdzenie pozycji 100%
  - Synchronizacja nawet po restartach HA
  - Tolerancja na zmiany czasu jazdy
- **Przykład:** `"ns=2;s=Sensor_Open"`

#### `fully_closed_nodeid`
- **Typ:** `string` (OPC-UA NodeID)
- **Opis:** Node czujnika osiągnięcia pełnego zamknięcia
- **Czytane Wartości:**
  - `True` - roletka całkowicie zamknięta
  - `False` - roletka nie jest całkowicie zamknięta
- **Wymagana?** ❌ NIE (ale bardzo zalecana)
- **Korzyści:**
  - Precyzyjne potwierdzenie pozycji 0%
  - Synchronizacja nawet po restartach HA
  - Tolerancja na zmiany czasu jazdy
- **Przykład:** `"ns=2;s=Sensor_Closed"`

---

### 🔵 OPCJONALNE (IDENTYFIKACJA)

#### `unique_id`
- **Typ:** `string`
- **Opis:** Unikalny identyfikator entity'a w Home Assistant
- **Wymagana?** ❌ NIE (ale zalecana)
- **Dlaczego?**
  - Pozwala na zmianę nazwy bez utraty historii
  - Umożliwia migrację entity'a
  - Zapewnia stabilność między aktualizacjami
- **Wymagania:**
  - Musi być unikalny w obrębie całego HA
  - Powinien być stabilny (nie zmieniać się)
- **Format:** lowercase + underscores
- **Przykład:** `"cover_living_room"`, `"cover_bedroom_left_blind"`

---

## Kombinacje i Scenariusze

### Scenariusz 1: Minimalna Konfiguracja

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Roletka Prosta"
        hub: "hub"
        nodeid: "ns=2;s=blind"
        open_nodeid: "ns=2;s=open"
        close_nodeid: "ns=2;s=close"
        travelling_time_down: 30
        travelling_time_up: 30
```

**Zachowanie:**
- Pozycja obliczana na podstawie czasu
- Brak czujników końcowych
- Po restarcie HA: używa ostatnio zapamiętanej pozycji

---

### Scenariusz 2: Ze Czujnikami

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Roletka ze Czujnikami"
        hub: "hub"
        nodeid: "ns=2;s=blind"
        open_nodeid: "ns=2;s=open"
        close_nodeid: "ns=2;s=close"
        travelling_time_down: 30
        travelling_time_up: 30
        fully_open_nodeid: "ns=2;s=sensor_open"
        fully_closed_nodeid: "ns=2;s=sensor_closed"
```

**Zachowanie:**
- Pozycja obliczana na podstawie czasu
- **Czujniki potwierddzają pozycje krańcowe**
- Po restarcie HA: synchronizuje się z czujnikami
- **Najniezawodniejsze podejście** ✅

---

### Scenariusz 3: Ze Sterowaniem i Sensorem Stopu

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Roletka Zaawansowana"
        hub: "hub"
        nodeid: "ns=2;s=blind"
        open_nodeid: "ns=2;s=motor_open"
        close_nodeid: "ns=2;s=motor_close"
        stop_nodeid: "ns=2;s=motor_stop"
        travelling_time_down: 28
        travelling_time_up: 32
        fully_open_nodeid: "ns=2;s=limit_open"
        fully_closed_nodeid: "ns=2;s=limit_close"
        unique_id: "cover_main_blind"
```

**Zachowanie:**
- Pełna kontrola (open, close, stop)
- Precyzyjne czujniki końcowe
- Stabilny unique_id
- **Główne zalecane ustawienie** ⭐

---

## Typowe Wartości

### Czasy Podróży

| Typ Roletki | Traveling Time Down | Traveling Time Up | Uwagi |
|-------------|-------------------|------------------|-------|
| Roletki zwierające | 20-30s | 20-30s | Symetryczne |
| Żaluzje drewniane | 15-25s | 15-25s | Lekkie |
| Rolety nailonowe | 25-35s | 25-35s | Średnie |
| Rolety ciężkie | 30-45s | 30-45s | Silniki wolne |
| Brama garażowa | 10-20s | 10-20s | Bardzo szybka |

---

## Wzór NodeID'ów

```
Otwarcie:
  ns=2;s=Motor_Open
  ns=2;s=Blind_Open
  ns=2;s=Roll_Up
  ns=2;s=Shutter_Open

Zamknięcie:
  ns=2;s=Motor_Close
  ns=2;s=Blind_Close
  ns=2;s=Roll_Down
  ns=2;s=Shutter_Close

Stop:
  ns=2;s=Motor_Stop
  ns=2;s=Blind_Stop
  ns=2;s=Roll_Stop

Czujniki:
  ns=2;s=Sensor_Open
  ns=2;s=Sensor_Closed
  ns=2;s=Switch_FullyOpen
  ns=2;s=Switch_FullyClosed
  ns=2;s=Limit_Open
  ns=2;s=Limit_Closed
```

---

## Validacja Konfiguracji

### Sprawdzenie Składni

```bash
# Home Assistant
Developer Tools → YAML → Check Configuration
```

### Sprawdzenie Działania

```yaml
# Developer Tools → Services
service: cover.open_cover
target:
  entity_id: cover.nazwa_roletki
```

---

## Migracja / Zmiana Konfiguracji

### Zmiana `travelling_time_down`

```yaml
# PRZED
travelling_time_down: 30

# ZMIERZ NOWY CZAS
# (np. rzeczywisty czas to 35 sekund)

# PO
travelling_time_down: 35

# Zrestartuj HA
```

### Dodanie Czujników

```yaml
# BYŁO
- name: "Roletka"
  hub: "hub"
  open_nodeid: "ns=2;s=open"
  close_nodeid: "ns=2;s=close"
  travelling_time_down: 30
  travelling_time_up: 30

# STAŁO SIĘ
- name: "Roletka"
  hub: "hub"
  open_nodeid: "ns=2;s=open"
  close_nodeid: "ns=2;s=close"
  travelling_time_down: 30
  travelling_time_up: 30
  fully_open_nodeid: "ns=2;s=sensor_open"        # ← DODANE
  fully_closed_nodeid: "ns=2;s=sensor_closed"    # ← DODANE

# Zrestartuj HA
```

---

## Format NodeID'ów - Szczegóły

### Namespace Index (`ns`)
- `ns=0` - Standard nodes (sieci, properties)
- `ns=1` - Custom implementation
- `ns=2`, `ns=3`, itd. - Manufacturer specific

### Identifier Types

```yaml
# String identifier
ns=2;s=MyMotor
ns=2;s=Cover_Living_Room

# Integer identifier
ns=2;i=1000
ns=2;i=5001

# GUID identifier
ns=3;g=12345678-1234-1234-1234-123456789012

# Opaque (binary)
ns=2;b=...

# Fully qualified (rzadko)
nsu=http://example.com;s=Cover1
```

**Gdzie znaleźć?** OPC-UA Explorer albo dokumentacja sterownika

---

## Best Practices

1. ✅ Zawsze ustaw `unique_id`
2. ✅ Zawsze dodaj `fully_open_nodeid` i `fully_closed_nodeid`
3. ✅ Zmierz dokładnie czasy jazdy
4. ✅ Testuj każdą roletę indywidualnie
5. ✅ Używaj zrozumiałych nazw
6. ✅ Dokumentuj swoje node'y

---

**Wersja:** 1.0  
**Data:** 2026-01-11
