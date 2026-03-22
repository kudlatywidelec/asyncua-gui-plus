# Quickstart - Roletki Asyncua (Cover)

## 🚀 Szybki Start w 5 Minut

### Krok 1: Upewnij się że Hub Jest Skonfigurowany

```yaml
# configuration.yaml
asyncua:
  - name: "moj_hub"
    url: "opc.tcp://192.168.1.100:4840"
    scan_interval: 30
```

### Krok 2: Dodaj Roletę

```yaml
# configuration.yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Moja Roletka"
        hub: "moj_hub"
        nodeid: "ns=2;s=Roletka1"
        travelling_time_down: 30
        travelling_time_up: 30
        open_nodeid: "ns=2;s=Roletka1_Open"
        close_nodeid: "ns=2;s=Roletka1_Close"
```

### Krok 3: Zrestartuj Home Assistant

```
Developer Tools → YAML → Restart
```

### Krok 4: Przetestuj

```yaml
# Developer Tools → Services
service: cover.open_cover
target:
  entity_id: cover.moja_roletka
```

✅ **Gotowe!**

---

## 📋 Obowiązkowe Parametry

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Nazwa Roletki"                    # ← Wyświetlana nazwa
        hub: "moj_hub"                           # ← Nazwa hub'a z asyncua
        nodeid: "ns=2;s=..."                     # ← Node ID roletki
        travelling_time_down: 30                 # ← Czas zamknięcia (sek)
        travelling_time_up: 30                   # ← Czas otwarcia (sek)
        open_nodeid: "ns=2;s=..."                # ← Polecenie otwarcia
        close_nodeid: "ns=2;s=..."               # ← Polecenie zamknięcia
```

---

## 🎛️ Opcjonalne Parametry

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "..."
        hub: "..."
        nodeid: "..."
        travelling_time_down: 30
        travelling_time_up: 30
        open_nodeid: "..."
        close_nodeid: "..."
        stop_nodeid: "ns=2;s=..."                # ← Polecenie STOP
        fully_open_nodeid: "ns=2;s=..."          # ← Czujnik otwarcia
        fully_closed_nodeid: "ns=2;s=..."        # ← Czujnik zamknięcia
        unique_id: "roletka_sala"                # ← Stabilny ID
```

---

## 🔍 Co to znaczy?

| Parametr | Znaczenie | Przykład |
|----------|-----------|---------|
| `name` | Nazwa w UI | `"Roletka Salon"` |
| `hub` | Hub OPCUA | `"dom_hub"` |
| `nodeid` | ID roletki | `"ns=2;s=blind_1"` |
| `travelling_time_down` | Czas zamknięcia z 0% do 100% | `30` (sekund) |
| `travelling_time_up` | Czas otwarcia z 100% do 0% | `35` (sekund) |
| `open_nodeid` | Node do wysyłania polecenia otwórz | `"ns=2;s=open"` |
| `close_nodeid` | Node do wysyłania polecenia zamknij | `"ns=2;s=close"` |
| `stop_nodeid` | Node do wysyłania polecenia stop (opcja) | `"ns=2;s=stop"` |
| `fully_open_nodeid` | Czujnik: roletka całkowicie otwarta | `"ns=2;s=open_sensor"` |
| `fully_closed_nodeid` | Czujnik: roletka całkowicie zamknięta | `"ns=2;s=closed_sensor"` |

---

## 💡 Jak Zmierzyć Czas Jazdy?

### Dla `travelling_time_down` (zamknięcie):

1. Otwórz roletę na 100%
2. Kliknij CLOSE i zmierz czas do całkowitego zamknięcia
3. Ustaw tę wartość w `travelling_time_down`

```yaml
travelling_time_down: 28  # Zmierzyłem 28 sekund
```

### Dla `travelling_time_up` (otwarcie):

1. Zamknij roletę na 0%
2. Kliknij OPEN i zmierz czas do całkowitego otwarcia
3. Ustaw tę wartość w `travelling_time_up`

```yaml
travelling_time_up: 32    # Zmierzyłem 32 sekundy
```

---

## 🎮 Jak Sterować?

### Z UI (Visual)

Home Assistant → Entities → cover.moja_roletka
- 🔼 OPEN - całkowicie otworzy
- 🔽 CLOSE - całkowicie zamknie
- ⏹️ STOP - zatrzyma
- Slider (50%) - ustaw konkretną pozycję

### Z Automatyzacji (YAML)

```yaml
# Całkowicie otworzyć
- service: cover.open_cover
  target:
    entity_id: cover.moja_roletka

# Całkowicie zamknąć
- service: cover.close_cover
  target:
    entity_id: cover.moja_roletka

# Zatrzymać
- service: cover.stop_cover
  target:
    entity_id: cover.moja_roletka

# Ustawić na 50%
- service: cover.set_cover_position
  target:
    entity_id: cover.moja_roletka
  data:
    position: 50

# Resetować na 100% (otwarta)
- service: asyncua_cover.reset_fully_open
  target:
    entity_id: cover.moja_roletka

# Resetować na 0% (zamknięta)
- service: asyncua_cover.reset_fully_closed
  target:
    entity_id: cover.moja_roletka
```

---

## 🧪 Jak Znaleźć Node ID'y?

### Metoda 1: OPC-UA Explorer (na Windows/Linux)

1. Pobierz: [Softing OPC-UA Explorer](https://www.softing.com/en/industrial-automation/products/opc-ua/opc-ua-explorer.html)
2. Połącz się do sterownika: `opc.tcp://IP:4840`
3. Przeglądaj drzewo węzłów
4. Skopiuj pełny NODEID (np. `ns=2;s=Motor_Open`)

### Metoda 2: Z Dokumentacji Sterownika

Producent zwykle dostarcza mapę node'ów. Szukaj:
- `Open` lub `Motor_Open` → `open_nodeid`
- `Close` lub `Motor_Close` → `close_nodeid`
- `Stop` lub `Motor_Stop` → `stop_nodeid`
- `OpenSensor` lub `EndStop_Open` → `fully_open_nodeid`
- `ClosedSensor` lub `EndStop_Closed` → `fully_closed_nodeid`

### Metoda 3: Pytanie Dostawcy

Jeśli masz dostawcę sterownika, poproś o:
- Mapę node'ów OPCUA
- Opis poleceń sterowania (otwórz, zamknij, stop)
- Node'y czujników (jeśli dostępne)

---

## ❌ Typowe Błędy

### ❌ `Asyncua hub not found`

```
Asyncua hub moj_hub not found. Specify a valid asyncua hub in the configuration.
```

**Przyczyna:** Nazwa hub'a w `cover` nie zgadza się z nazwą w `asyncua`

**Rozwiązanie:**
```yaml
asyncua:
  - name: "moj_hub"    # ← Musi być tutaj

cover:
  - platform: asyncua
    nodes:
      - hub: "moj_hub"  # ← Taka sama nazwa
```

---

### ❌ Roletka się nie porusza

**Przyczyna:** Błędne NODEID'y polecenia

**Sprawdzenie:**
1. Potwierdzić NODEID'y w OPC-UA Explorer
2. Sprawdzić logi:
   ```yaml
   logger:
     logs:
       asyncua: debug
   ```
3. Szukać: `Sending command ... to node`

---

### ❌ Pozycja się zmienia bardzo powoli/szybko

**Przyczyna:** Błędny `travelling_time_down`/`travelling_time_up`

**Rozwiązanie:** Ponownie zmierz czas i zaktualizuj

```yaml
# Zmierz czasami o ile czasu zajmuje otwarcie/zamknięcie
travelling_time_down: NOWA_WARTOŚĆ
travelling_time_up: NOWA_WARTOŚĆ
```

---

## 📚 Pełna Dokumentacja

Pełna dokumentacja ze wszystkimi szczegółami: [COVER_CONFIGURATION.md](./COVER_CONFIGURATION.md)

Tam znajdziesz:
- ✅ Wszystkie parametry
- ✅ Zaawansowane przykłady
- ✅ Troubleshooting
- ✅ Automatyzacje

---

## 🎯 Następne Kroki

1. ✅ Skonfiguruj hub
2. ✅ Dodaj 1 roletę
3. ✅ Przetestuj sterowanie
4. ✅ Dodaj pozostałe roletki
5. ✅ Utwórz automatyzacje
6. 📖 Przeczytaj pełną dokumentację

---

**Potrzebujesz pomocy?**
- Logi: `Developer Tools → Logs`
- Debugowanie: [COVER_CONFIGURATION.md - Troubleshooting](./COVER_CONFIGURATION.md#rozwiązywanie-problemów)
- GitHub: [Issues](https://github.com/kudlatywidelec/asyncua-gui-plus/issues)
