# Config Flow dla Asyncua

## ✅ Dodano Graficzny Interfejs Konfiguracji

Asyncua teraz posiada **Config Flow** - możliwość konfiguracji poprzez graficzny interfejs Home Assistant.

---

## 🎯 Jak Używać Config Flow

### Metoda 1: Przez UI Home Assistant

1. Idź do **Settings → Devices & Services**
2. Kliknij **+ Create Automation**
3. Szukaj **"Asyncua"**
4. Wprowadź parametry hub'u

### Metoda 2: Przez URL

```
http://twoje-ha.local:8123/config/integrations/create?domain=asyncua
```

---

## 📝 Parametry Config Flow

| Parametr | Wymagany | Typ | Opis |
|----------|----------|-----|------|
| **Hub Name** | ✅ | string | Unikalna nazwa hub'u (np. "dom_hub") |
| **Server URL** | ✅ | string | Adres OPCUA (np. "opc.tcp://192.168.1.100:4840") |
| **Manufacturer** | ❌ | string | Producent urządzenia (opcjonalny) |
| **Model** | ❌ | string | Model urządzenia (opcjonalny) |
| **Username** | ❌ | string | Nazwa użytkownika (jeśli wymagana) |
| **Password** | ❌ | string | Hasło (jeśli wymagane) |
| **Scan Interval** | ❌ | integer | Interwał aktualizacji w sekundach (domyślnie: 30) |

---

## ✨ Cechy Config Flow

✅ **Walidacja URL**
- Sprawdza czy URL to `opc.tcp://...`
- Sprawdza czy zawiera host i port

✅ **Zapobieganie Duplikatom**
- Nie pozwala na dodanie hub'u o tej samej nazwie
- Używa `unique_id` do identyfikacji

✅ **Intuicyjny Interfejs**
- Pola wymagane vs opcjonalne
- Domyślne wartości
- Opisy pól

---

## 🔄 YAML vs Config Flow

### YAML (Stary Sposób)

```yaml
asyncua:
  - name: "moj_hub"
    url: "opc.tcp://192.168.1.100:4840"
    scan_interval: 30
```

### Config Flow (Nowy Sposób)

1. Kliknij "+ Create Integration"
2. Wypełnij formularz
3. Kliknij "Create"
4. ✅ Gotowe!

**Oba sposoby działają jednocześnie!** 🎯

---

## 🧪 Testowanie

Po dodaniu hub'u przez Config Flow:

1. Sprawdź czy pojawia się w **Devices & Services**
2. Sprawdź logi:
   ```
   Settings → Logs → Szukaj "asyncua"
   ```
3. Sprawdź czy sensor'y/switch'e/cover'y się ładują

---

## ⚙️ Implementacja

### Pliki Zmienione

1. **config_flow.py**
   - `AsyncuaConfigFlow` - klasa config flow
   - `async_step_user()` - formularz użytkownika
   - `_async_validate_input()` - walidacja
   - `CannotConnect` - wyjątek

2. **strings.json**
   - Dodano sekcję `config`
   - Opisy pól w UI
   - Komunikaty błędów

3. **const.py**
   - Używane istniejące stałe

---

## 📍 Jak To Działa

```
Użytkownik kliknął "+ Create Integration"
    ↓
async_step_user() wyświetla formularz
    ↓
Użytkownik wypełnia parametry
    ↓
async_set_unique_id() sprawdza duplikaty
    ↓
_async_validate_input() waliduje URL
    ↓
async_create_entry() zapisuje konfigurację
    ↓
Hub pojawia się w Devices & Services
    ↓
Sensory/Switch'e/Cover'y są automatycznie ładowane
```

---

## 🔐 Bezpieczeństwo

- Hasła są **szyfrowane** przez Home Assistant
- Config Flow używa **HTTPS**
- Dane przechowywane w `.storage/asyncua` (zaszyfrowane)

---

## 📚 Więcej Informacji

- [Home Assistant Config Flow Documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Asyncua YAML Configuration](./COVER_CONFIGURATION.md)

---

**Wersja:** 1.0  
**Data:** 2026-01-11
