# Asyncua OPC-UA Integration for Home Assistant

A Home Assistant integration that provides connectivity to OPC-UA (OPC Unified Architecture) servers using the asyncua library. This integration allows you to monitor and control industrial equipment, PLC systems, and other OPC-UA enabled devices directly from Home Assistant.

## Features

- **Hub Integration**: Connect to OPC-UA servers with configurable scan intervals
- **Four Entity Types**: Sensor, Binary Sensor, Switch, and Cover platforms
- **Dynamic Entity Management**: Add/delete/modify entities via the UI without restart (Options Flow)
- **Node ID Validation**: Validates OPC-UA node ID format before configuration (ns=X;s=... or ns=X;i=...)
- **Device Integration**: Automatic device registry support with unique IDs
- **Coordinator Pattern**: Efficient, centralized data polling via DataUpdateCoordinator
- **Multiple Hubs**: Support multiple OPC-UA connections in a single Home Assistant instance
- **Named Entities**: Modern entity naming with `has_entity_name` support

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Explore & Download Repositories"
3. Search for "asyncua"
4. Click "Install"
5. Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `asyncua` folder to `config/custom_components/`
3. Restart Home Assistant

## Quick Start - Configuration Flow UI

The easiest way to set up asyncua is through the UI:

1. Go to **Settings → Devices & Services**
2. Click **Create Integration**
3. Search for and select **"asyncua"**
4. Fill in the OPC-UA server details:
   - **Hub Name**: `plc_15` (or your preferred name)
   - **Server URL**: `opc.tcp://192.168.2.15:4840` (your OPC-UA server)
   - **Scan Interval**: `30` (seconds - default is fine)
   - Username/Password: Only if your server requires authentication

5. After creating the hub, click **Options** to add entities:
   - **Add a new sensor** - Read numeric/text values
   - **Add a new binary sensor** - Read boolean states
   - **Add a new switch** - Control binary outputs
   - **Add a new cover** - Control roller blinds/shutters

## OPC-UA Node ID Format

Node IDs must follow OPC-UA standard format:

```
ns=NAMESPACE;TYPE=IDENTIFIER
```

Where:
- `ns=2` = Namespace (typically 2 for server-defined nodes)
- `s=` = String identifier (text)
- `i=` = Numeric identifier (integer)

**Valid Examples:**
```
ns=2;s=zmienna
ns=2;s=TemperatureSensor
ns=2;s=/PLC/Devices/Pump1/Status
ns=2;i=2005
```

**To find your Node IDs:**
1. Use the [UaExpert OPC-UA Client](https://www.unified-automation.com/products/development-tools/uaexpert)
2. Use the [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui)
3. Check your PLC/OPC-UA server documentation

## Detailed Configuration

### Adding a Sensor

Example: Read temperature from a Siemens PLC

1. Go to Options for your asyncua hub
2. Click **"Add a new sensor"**
3. Fill in:
   - **Sensor Name**: `Living Room Temperature`
   - **Node ID**: `ns=2;s=Temperature_Room1`
   - **Device Class**: `temperature` (optional)
   - **State Class**: `measurement` (default)
   - **Unit**: `°C` (optional)
4. Click Submit - hub automatically reloads

Your sensor will appear as `sensor.living_room_temperature` (entity_id auto-generated)

### Adding a Binary Sensor

Example: Monitor a door sensor

1. Go to Options → **"Add a new binary sensor"**
2. Fill in:
   - **Name**: `Front Door`
   - **Node ID**: `ns=2;s=DoorOpen_1`
   - **Device Class**: `door` (optional - shows door icon)
3. Submit

Entity appears as `binary_sensor.front_door`

### Adding a Switch

Example: Control a pump

1. Go to Options → **"Add a new switch"**
2. Fill in:
   - **Name**: `Circulation Pump`
   - **Node ID**: `ns=2;s=Pump_Command`
   - **Readback Node** (optional): `ns=2;s=Pump_Status` (shows actual state)
3. Submit

Entity appears as `switch.circulation_pump`

The readback node is useful if your command output is separate from the status feedback (common in industrial PLC).

### Adding a Cover (Roller Blind/Shutter)

Example: Control a roller blind with position tracking

1. Go to Options → **"Add a new cover"**
2. Fill in:
   - **Name**: `Living Room Blind`
   - **Position/ID Node**: `ns=2;s=Blind_Pos_1` (position tracking)
   - **Open Command Node**: `ns=2;s=Blind_Open_Cmd` (set True to open)
   - **Close Command Node**: `ns=2;s=Blind_Close_Cmd` (set True to close)
   - **Stop Command Node** (optional): `ns=2;s=Blind_Stop_Cmd`
   - **Fully Open Sensor** (optional): `ns=2;s=Blind_Fully_Open`
   - **Fully Closed Sensor** (optional): `ns=2;s=Blind_Fully_Closed`
   - **Travel Time Down**: `25` seconds (fully close time)
   - **Travel Time Up**: `25` seconds (fully open time)
3. Submit

Entity appears as `cover.living_room_blind`

The integration calculates blind position based on travel time. Position sensors (fully_open/fully_closed) help calibrate the position.

## Entity Naming Convention

This integration uses Home Assistant's modern naming: **has_entity_name = True**

- **Entity Name**: Only the data point (e.g., "Temperature", "Door Status")
- **Device Name**: The hub name (e.g., "PLC 15")
- **Friendly Name**: Combined (e.g., "PLC 15 Temperature")
- **Entity ID**: Auto-generated (e.g., `sensor.plc_15_temperature`)

## Managing Entities

### Adding Entities
- Go to **Settings → Devices & Services**
- Find your asyncua hub
- Click **Options**
- Select the entity type to add

### Deleting Entities
- Go to Options → **"Manage entities"**
- Select the entity to delete
- Choose "Delete"
- Hub automatically reloads

### Editing Entities
- Delete the entity (see above)
- Re-add with updated configuration

## YAML Configuration (Advanced)

While the UI is recommended, YAML configuration is still supported for advanced users:

```yaml
asyncua:
  - name: plc_15
    url: opc.tcp://192.168.2.15:4840
    scan_interval: 30
    username: admin
    password: password123
    manufacturer: Siemens
    model: S7-1200

sensor:
  - platform: asyncua
    hub: plc_15
    nodes:
      - name: Temperature
        unique_id: temp_sensor_1
        nodeid: ns=2;s=temperature_pv
        device_class: temperature
        state_class: measurement
        unit_of_measurement: "°C"

binary_sensor:
  - platform: asyncua
    hub: plc_15
    nodes:
      - name: Door Open
        unique_id: door_sensor_1
        nodeid: ns=2;s=door_status
        device_class: door

switch:
  - platform: asyncua
    hub: plc_15
    nodes:
      - name: Pump
        unique_id: pump_switch_1
        nodeid: ns=2;s=pump_command

cover:
  - platform: asyncua
    hub: plc_15
    nodes:
      - name: Blind
        unique_id: blind_cover_1
        nodeid: ns=2;s=blind_position
        travelling_time_down: 25
        travelling_time_up: 25
        open_nodeid: ns=2;s=blind_open
        close_nodeid: ns=2;s=blind_close
        stop_nodeid: ns=2;s=blind_stop
```

## Troubleshooting

### Connection Issues

**"Failed to connect to OPC-UA server"**
- Verify URL format: `opc.tcp://hostname_or_ip:port`
- Check OPC-UA server is running
- Check firewall allows connection
- Test with an OPC-UA client tool first

### Invalid Node ID Format

**"Invalid OPC-UA node ID format. Use ns=X;s=... or ns=X;i=..."**
- Node ID must start with `ns=NUMBER`
- Must contain either `s=` (string) or `i=` (numeric)
- Example: `ns=2;s=MyVariable`
- Use OPC-UA browser to find correct IDs

### Entities Not Updating

**Sensor values don't change**
- Increase scan_interval if too frequent
- Verify node IDs exist on server
- Check Home Assistant logs: **Settings → System → Logs**
- Restart the asyncua integration

### "ConfigEntryAuthFailed"

**Authentication error**
- Verify username and password
- Some servers allow empty credentials
- Check server security settings

## Home Assistant Integration Services

The integration provides a service to set OPC-UA node values:

```yaml
service: asyncua.set_value
data:
  hub: plc_15
  nodeid: ns=2;s=OutputValue
  value: 42.5
```

This is useful for automation and manual control beyond the standard entity services.

## Architecture

### Components

- **AsyncuaHub**: Manages OPC-UA client and connection lifecycle
- **AsyncuaCoordinator**: DataUpdateCoordinator for periodic polling
- **Entities**: Sensor, BinarySensor, Switch, Cover - all CoordinatorEntity subclasses
- **Device Registry**: Automatic device tracking with unique_ids

### Data Flow

1. Hub connects to OPC-UA server
2. Coordinator polls nodes on schedule (scan_interval)
3. Entities read from coordinator.data
4. Coordinator notifies entities of updates
5. Entities write state to Home Assistant

## Home Assistant Compatibility

- **Minimum HA Version**: 2024.1+
- **Python Version**: 3.11+
- **Asyncua Library**: 1.0.2

## Credits

- [FreeOpcUa asyncua](https://github.com/FreeOpcUa/opcua-asyncio) - OPC-UA client library
- Home Assistant community for integration patterns

## License

This integration uses the asyncua library (LGPL). See [LICENSE](LICENSE) for details.

## Support & Issues

Found a bug? Have a feature request?
- GitHub Issues: https://github.com/KVSoong/asyncua/issues
- Home Assistant Community: https://community.home-assistant.io/

## Changelog

### v0.1.2
- Added OPC-UA node ID validation in UI forms
- Added entity deletion/management via Options Flow
- Improved entity naming with `has_entity_name` pattern
- Enhanced unique ID generation (format: `hub_nodeid`)
- Fixed entity initialization and coordinator updates

### v0.1.1
- Initial release
- Support for Sensor, Binary Sensor, Switch, Cover platforms
- Options Flow for dynamic entity management
- Config Flow for hub setup
sensor:
  - platform: asyncua
    nodes:
      - name: "Temperatura Pomieszczenia"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=Temperature"
        device_class: "temperature"
        unit_of_measurement: "°C"
        state_class: "measurement"
```

[Dokumentacja Sensor →](./SENSOR_CONFIGURATION.md)

---

### Czujniki Binarne (Binary Sensor)

Odczyt stanów logicznych (włączone/wyłączone):

```yaml
binary_sensor:
  - platform: asyncua
    nodes:
      - name: "Drzwi Otwarte"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=DoorOpen"
        device_class: "door"
```

[Dokumentacja Binary Sensor →](./BINARY_SENSOR_CONFIGURATION.md)

---

### Wyłączniki (Switch)

Sterowanie przełącznikami:

```yaml
switch:
  - platform: asyncua
    nodes:
      - name: "Pompa Wody"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=PumpControl"
```

[Dokumentacja Switch →](./SWITCH_CONFIGURATION.md)

---

### Roletki (Cover)

Sterowanie roletami i żaluzjami z obliczaniem pozycji czasowej:

```yaml
cover:
  - platform: asyncua
    nodes:
      - name: "Żaluzja Salon"
        hub: "my_opcua_hub"
        nodeid: "ns=2;s=LivingRoomBlind"
        travelling_time_down: 30
        travelling_time_up: 30
        open_nodeid: "ns=2;s=Blind_Open"
        close_nodeid: "ns=2;s=Blind_Close"
```

[📖 Dokumentacja Cover →](./COVER_CONFIGURATION.md) ⭐ **PEŁNA DOKUMENTACJA**

---

## Service Calls

### Service: `asyncua.set_value`

Wysyła wartość do node'a OPCUA:

```yaml
service: asyncua.set_value
data:
  hub: "my_opcua_hub"
  nodeid: "ns=2;s=SomeNode"
  value: 123
```

**Obsługiwane typy wartości:**
- Liczby całkowite (int): `123`
- Liczby zmiennoprzecinkowe (float): `12.5`
- Łańcuchy tekstu (string): `"wartość"`
- Wartości logiczne (bool): `true` / `false`
- Bajty (bytes): `[0xFF, 0x00]`
- Czas (time): `"12:30:45"`

---

## Pliki Dokumentacji

| Plik | Opis |
|------|------|
| [COVER_CONFIGURATION.md](./COVER_CONFIGURATION.md) | 📖 **Pełna dokumentacja rolet** - parametry, przykłady, troubleshooting |
| [SENSOR_CONFIGURATION.md](./SENSOR_CONFIGURATION.md) | Dokumentacja sensorów |
| [BINARY_SENSOR_CONFIGURATION.md](./BINARY_SENSOR_CONFIGURATION.md) | Dokumentacja czujników binarnych |
| [SWITCH_CONFIGURATION.md](./SWITCH_CONFIGURATION.md) | Dokumentacja wyłączników |

---

## Struktura Plików

```
asyncua/
├── __init__.py                    # Inicjalizacja, coordinator, OpcuaHub
├── config_flow.py                 # Config flow (jeśli używany)
├── const.py                       # Stałe konfiguracyjne
├── sensor.py                      # Platforma sensor
├── binary_sensor.py               # Platforma binary_sensor
├── switch.py                      # Platforma switch
├── cover.py                       # Platforma cover (NOWE!)
├── travelcalculator.py           # Kalkulator pozycji rolet (NOWE!)
├── manifest.json                  # Metadane integracji
├── strings.json                   # Tłumaczenia
├── services.yaml                  # Definicje service'ów
├── COVER_CONFIGURATION.md         # Dokumentacja rolet (NOWE!)
└── README.md                      # Ten plik
```

---

## Przykłady Automatyzacji

### Zamknięcie Wszystkich Rolet o Zachodzie Słońca

```yaml
automation:
  - alias: "Close blinds at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: cover.close_cover
      target:
        entity_id:
          - cover.living_room_blind
          - cover.bedroom_blind
          - cover.kitchen_blind
```

### Resetowanie Pozycji Rolet rano

```yaml
automation:
  - alias: "Reset blinds position at morning"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      service: asyncua_cover.reset_fully_open
      target:
        entity_id:
          - cover.living_room_blind
```

### Ustawienie Rolet na 50% gdy wychodzisz

```yaml
automation:
  - alias: "Half-close blinds when leaving"
    trigger:
      platform: state
      entity_id: person.john
      to: "not_home"
    action:
      service: cover.set_cover_position
      target:
        entity_id: cover.living_room_blind
      data:
        position: 50
```

---

## Diagnostyka i Debug

### Włączenie Debug Logging

```yaml
logger:
  logs:
    asyncua: debug
    homeassistant.components.asyncua: debug
```

### Sprawdzenie Stanu Sensor'ów

```yaml
# W Developer Tools → States
# Szukaj entity'ów zaczynających się od:
# - sensor.asyncua_*
# - binary_sensor.asyncua_*
# - switch.asyncua_*
# - cover.asyncua_*
```

---

## Wymagania

- Home Assistant 2021.1 lub nowsze
- Python 3.8+
- Biblioteka `asyncua` (automatycznie instalowana)

---

## Kompatybilność

- ✅ Sterowniki Siemens S7-1200/1500
- ✅ Sterowniki Beckhoff TwinCAT
- ✅ Sterowniki GE Automation
- ✅ Inne urządzenia z OPC-UA (zależy od implementacji)

---

## Rozwiązywanie Problemów

### Roletka się nie porusza

1. Sprawdź czy hub jest dostępny:
   ```bash
   ping IP_STEROWNIKA
   ```

2. Sprawdź NODEID'y w sterownikiem (OPC-UA Explorer)

3. Sprawdź logi:
   ```yaml
   logger:
     logs:
       asyncua: debug
   ```

### Pozycja się nie synchronizuje

- Ustaw prawidłowe `travelling_time_down` i `travelling_time_up`
- Dodaj czujniki końcowe: `fully_open_nodeid`, `fully_closed_nodeid`

### Hub się rozłącza

- Sprawdź timeout w konfiguracji
- Sprawdzić firewall między HA a sterownikiem
- Zwiększyć `scan_interval` jeśli sieć jest wolna

---

## Problemy i Zgłaszanie Błędów

Aby zgłosić problem:

1. Włącz debug logging
2. Reprodukuj problem
3. Zbierz logi
4. Zgłoś na GitHub: [KVSoong/asyncua](https://github.com/KVSoong/asyncua/issues)

---

## Licencja

Patrz `LICENSE` w głównym repozytorium.

---

## Wersja

**asyncua** v0.1.2+ (z cover'ami)

**Data ostatniej aktualizacji:** 2026-01-11
