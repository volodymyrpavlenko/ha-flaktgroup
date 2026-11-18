# FläktGroup for Home Assistant

<img src="custom_components/flaktgroup/brand/icon.png" alt="FläktGroup" width="64" align="right">

Monitor and control your **FläktGroup RDKS** ventilation unit from Home Assistant. The integration talks directly to the unit over **Modbus TCP** on your local network. Setup requires the unit's network address and no cloud account.

[Installation](#installation) · [Configuration](#configuration) · [Entities and controls](#entities-and-controls) · [Help](#help) · [Contributing](#contributing)

## Compatibility

| Requirement | Details |
| --- | --- |
| Home Assistant | 2026.11.2 or newer |
| Ventilation unit | FläktGroup RDKS, verified on live hardware for setup, readings, and the Configure menu |
| Connection | Modbus TCP reachable from Home Assistant, with device ID `2` |

## Installation

### Manual installation

1. Copy the entire [`custom_components/flaktgroup`](custom_components/flaktgroup/) folder into your Home Assistant configuration directory. The manifest should end up at `<config>/custom_components/flaktgroup/manifest.json`, where `<config>` contains `configuration.yaml`.
2. Restart Home Assistant.
3. Add the integration using the steps below.

### Marketplace

Marketplace installation will be available once the repository is published on public GitHub. In **Settings → Marketplace → Add from link**, enter the public repository URL, then open the FläktGroup listing and select **Install**. [Home Assistant Marketplace guide](https://www.home-assistant.io/integrations/marketplace/#custom-repositories)

## Configuration

1. Go to **Settings → Devices & services → Add integration** and search for **FläktGroup**.
2. Enter the following values and submit the form. Home Assistant reads the unit's operating preset to confirm it can communicate over Modbus.

| Field | Value |
| --- | --- |
| Name | A friendly name, such as `RDKS` |
| Host | The unit's IP address or hostname |
| Port | `8899` by default |
| Update interval | `15` seconds by default |

### Upgrading from the Home Assistant Core fork

Back up Home Assistant, keep the existing FläktGroup config entry, and install the custom integration before starting the supported stock Home Assistant version. The integration migrates its internal registry IDs. Check the existing entity IDs and any automations that use them after startup.

## Entities and controls

| Where | What you can do |
| --- | --- |
| **Climate entity** | Change the temperature setpoint or operating preset. Adjust the fan speed in Manual mode. |
| **Sensors** | Read supply, extract, and outdoor temperatures, plus humidity, CO₂, airflow, and fan output where available. |
| **Binary sensors** | Monitor unit signals and alarms, including dirty filter, fan faults, and frost protection. Some entities are disabled by default and can be enabled from the device page. |
| **Configure menu** | Edit supply and extract fan speed profiles, temperature settings, the CO₂ setpoint, and the dirty-filter alarm interval. |

Open the settings menu under **Settings → Devices & services → FläktGroup → Configure**.

For automations that call climate actions, the mode values are numeric strings:

| Control | Values |
| --- | --- |
| Preset | `"0"` Stop, `"1"` Auto, `"2"` Manual, `"3"` Fireplace |
| Fan mode | `"0"` Low, `"1"` Normal, `"2"` High |

<details>
<summary>Example automation action for manual fan speed</summary>

This sequence selects Manual and then sets Low. Replace the example entity ID with your climate entity. Selecting Manual changes the unit's operating preset.

```yaml
actions:
  - action: climate.set_preset_mode
    target:
      entity_id: climate.rdks
    data:
      preset_mode: "2"
  - action: climate.set_fan_mode
    target:
      entity_id: climate.rdks
    data:
      fan_mode: "0"
```

</details>

## Help

- **Setup cannot connect.** Check the hostname and port from the Home Assistant host or container. A TCP connection alone is insufficient. The unit needs to answer the preset register read on Modbus device ID `2`.
- **An individual entity is missing or unavailable.** Check whether the entity is enabled and whether your unit exposes its register. Optional registers can vary across units.
- **A settings save fails.** The integration stops the group update on the first failed write and rereads the settings. Review the displayed values before retrying, since earlier writes may already have reached the unit.

For a bug report, include your Home Assistant version, integration version or commit, RDKS model and firmware if known, the steps to reproduce, and any `flaktgroup` or `pymodbus` messages from **Settings → System → Logs**. [Report an issue](https://gitlab.com/volodymyrpavlenko/ha-flaktgroup/-/issues)

## Contributing

The developer guide covers local setup, automated tests, an RDKS smoke test, and Marketplace releases. Include the Home Assistant version and, for changes to Modbus behavior, the register or firmware evidence in your pull request. [Developer guide](DEVELOPERS.md)

## Credits and license

The integration was imported from the Home Assistant Core fork's `flaktgroup_integration_all` branch at `8d9ea7363f2`. The original commits are recorded in the [developer guide](DEVELOPERS.md#source-history). The code is licensed under [Apache 2.0](LICENSE.md). The icon comes from the [FläktGroup website](https://www.flaktgroup.com/favicon.ico).
