# 📚 Dokumentacja Asyncua - Spis Treści

## 📖 Dokumentacja Cover (Roletki)

### 🚀 Dla Początkujących

1. **[QUICKSTART_COVER.md](./QUICKSTART_COVER.md)** ⭐ **ZACZNIJ TUTAJ**
   - Szybki start w 5 minut
   - Obowiązkowe parametry
   - Jak znaleźć Node ID'y
   - Typowe błędy

2. **[COVER_SCHEMA.md](./COVER_SCHEMA.md)**
   - Pełny schemat konfiguracji
   - Szczegóły każdego parametru
   - Kombinacje scenariuszy
   - Validacja konfiguracji

### 📖 Dla Zaawansowanych

3. **[COVER_CONFIGURATION.md](./COVER_CONFIGURATION.md)** ⭐ **PEŁNA DOKUMENTACJA**
   - Wprowadzenie
   - Wymagania
   - Parametry konfiguracji
   - Przykłady ustawień
   - Service Calls
   - Zasady działania
   - Rozwiązywanie problemów
   - Notatki

---

## 📦 Całe Integracje

### [README.md](./README.md)

Przegląd całej integracji Asyncua:
- ✅ Sensory (Sensor)
- ✅ Czujniki binarne (Binary Sensor)
- ✅ Wyłączniki (Switch)
- ✅ Roletki (Cover) **← NOWOŚĆ**
- 🔄 Coordinator pattern
- 📝 Przykłady automatyzacji
- 🔧 Diagnostyka

---

## 🎯 Szybka Nawigacja

### Mam problem

| Problem | Link |
|---------|------|
| Cover nie reaguje na polecenia | [COVER_CONFIGURATION.md#rozwiązywanie-problemów](./COVER_CONFIGURATION.md#rozwiązywanie-problemów) |
| Nie wiem jakie Node ID'y są potrzebne | [QUICKSTART_COVER.md#jak-znaleźć-node-id-y](./QUICKSTART_COVER.md#jak-znaleźć-node-id-y) |
| Pozycja się zmienia powoli/szybko | [COVER_CONFIGURATION.md#problem-pozycja-się-nie-zmienia-lub-zmienia-się-powoli](./COVER_CONFIGURATION.md#problem-pozycja-się-nie-zmienia-lub-zmienia-się-powoli) |
| Roletka zatrzymuje się w połowie | [COVER_CONFIGURATION.md#problem-roletka-zatrzymuje-się-w-połowie-drogi](./COVER_CONFIGURATION.md#problem-roletka-zatrzymuje-się-w-połowie-drogi) |
| Czujniki nie działają | [COVER_CONFIGURATION.md#problem-czujniki-nie-działają](./COVER_CONFIGURATION.md#problem-czujniki-nie-działają) |

### Chcę nauczyć się

| Temat | Link |
|-------|------|
| Szybki setup | [QUICKSTART_COVER.md](./QUICKSTART_COVER.md) |
| Parametry | [COVER_SCHEMA.md](./COVER_SCHEMA.md) |
| Przykłady | [COVER_CONFIGURATION.md#przykłady-ustawień](./COVER_CONFIGURATION.md#przykłady-ustawień) |
| Service Calls | [COVER_CONFIGURATION.md#service-calls](./COVER_CONFIGURATION.md#service-calls) |
| Automatyzacje | [README.md#przykłady-automatyzacji](./README.md#przykłady-automatyzacji) |

---

## 📋 Mapa Dokumentów

```
asyncua/
├── README.md                           ← Główny dokumentu integracji
├── COVER_CONFIGURATION.md              ← ⭐ PEŁNA DOKUMENTACJA COVER
├── COVER_SCHEMA.md                     ← Szczegóły parametrów
├── QUICKSTART_COVER.md                 ← 🚀 ZACZNIJ TUTAJ
├── DOCUMENTATION_INDEX.md              ← Ten plik
│
├── cover.py                            ← Kod cover'ów
├── travelcalculator.py                 ← Kalkulator pozycji
├── sensor.py                           ← Sensory
├── binary_sensor.py                    ← Czujniki binarne
├── switch.py                           ← Wyłączniki
├── __init__.py                         ← Hub i Coordinator
├── config_flow.py                      ← Config flow (UI)
├── const.py                            ← Stałe
├── manifest.json                       ← Metadane
├── strings.json                        ← Tłumaczenia
└── services.yaml                       ← Definicje service'ów
```

---

## 📚 Przewodniki Tematyczne

### Cover (Roletki) - Kompletny Przewodnik

**Nowy użytkownik?** 👇
```
1. Czytaj: QUICKSTART_COVER.md (5 minut)
2. Konfiguruj: Twój cover w configuration.yaml
3. Testujesz: Otwórz/zamknij cover
4. Czytaj szczegóły: COVER_SCHEMA.md
5. Dodaj czujniki: fully_open_nodeid, fully_closed_nodeid
6. Czytaj więcej: COVER_CONFIGURATION.md
```

**Doświadczony użytkownik?** 👇
```
1. Czytaj: COVER_SCHEMA.md (parametry)
2. Przegląd: COVER_CONFIGURATION.md (wszystkie cechy)
3. Troubleshoot: Sekcja rozwiązywania problemów
```

### Sensor / Binary Sensor / Switch

Patrz [README.md](./README.md) - sekcja dokumentacji dla każdej platformy

---

## 🔄 Wersjonowanie

| Komponent | Wersja | Dodano |
|-----------|--------|--------|
| asyncua | v0.1.2+ | Wsparcie cover'ów |
| cover | NEW | 2026-01-11 |
| travelcalculator | NEW | 2026-01-11 |

---

## 🎯 Checklist - Przed Wdrożeniem

- [ ] Przeczytam QUICKSTART_COVER.md
- [ ] Skonfigurowałem hub OPCUA
- [ ] Znalazłem Node ID'y (open, close, czujniki)
- [ ] Zmierzyłem travelling_time
- [ ] Dodałem cover do configuration.yaml
- [ ] Zrestartowałem HA
- [ ] Przetestowałem otwórz/zamknij
- [ ] Dodałem czujniki (opcjonalnie)
- [ ] Przeczytałem COVER_SCHEMA.md
- [ ] Skonfigurowałem unique_id

---

## 📞 Gdzie Szukać Pomocy?

1. **Dokumentacja** 📖
   - [COVER_CONFIGURATION.md - Troubleshooting](./COVER_CONFIGURATION.md#rozwiązywanie-problemów)
   - [QUICKSTART_COVER.md - Typowe Błędy](./QUICKSTART_COVER.md#-typowe-błędy)

2. **Home Assistant**
   - Developer Tools → Logs (szukaj "asyncua")
   - Developer Tools → Services (testuj)

3. **GitHub**
   - Issues: [kudlatywidelec/asyncua-gui-plus](https://github.com/kudlatywidelec/asyncua-gui-plus/issues)
   - Załącz: konfigurację, logi, błędy

---

## 🎓 Słownik

| Termin | Opis |
|--------|------|
| **Hub** | Połączenie do serwera OPCUA |
| **NODEID** | Unikalny identyfikator node'a w OPCUA |
| **travelling_time** | Czas pełnego przejazdu roletki |
| **fully_open_nodeid** | Czujnik: roletka całkowicie otwarta |
| **fully_closed_nodeid** | Czujnik: roletka całkowicie zamknięta |
| **Coordinator** | Manager pobierający dane z hub'a |
| **time-based positioning** | Obliczanie pozycji na podstawie czasu |
| **unique_id** | Stabilny identyfikator entity'a |

---

## ✨ Najważniejsze Pliki

| Plik | Dla Kogo | Zawartość |
|------|----------|-----------|
| **QUICKSTART_COVER.md** | Początkujących | 5-minutowy setup |
| **COVER_CONFIGURATION.md** | Zaawansowanych | Pełna dokumentacja |
| **COVER_SCHEMA.md** | Wszystkich | Szczegóły parametrów |
| **README.md** | Wszystkich | Przegląd integracji |

---

## 🚀 Szybkie Linki

```yaml
# Minimum konfiguracji
cover:
  - platform: asyncua
    nodes:
      - name: "Moja Roletka"
        hub: "moj_hub"
        nodeid: "ns=2;s=Cover1"
        open_nodeid: "ns=2;s=Cover1_Open"
        close_nodeid: "ns=2;s=Cover1_Close"
        travelling_time_down: 30
        travelling_time_up: 30
```

📖 Pełna dokumentacja: [COVER_CONFIGURATION.md](./COVER_CONFIGURATION.md)

---

**Ostatnia aktualizacja:** 2026-01-11  
**Autor:** Asyncua Integration  
**Wersja dokumentacji:** 1.0
