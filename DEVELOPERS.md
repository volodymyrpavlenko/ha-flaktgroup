# Developer guide

## Set up the workspace

Use Python 3.14 and Home Assistant 2026.11.2. The test dependency file pins Home Assistant’s pytest fixtures and the PyModbus version used by the integration.

```sh
uv venv --python 3.14
source .venv/bin/activate
uv pip install -r requirements-test.txt
ruff check .
ruff format --check .
pytest
```

## Find the code

| Area | Location |
| --- | --- |
| Config entries, migration, and platform lifecycle | [`__init__.py`](custom_components/flaktgroup/__init__.py) |
| Setup and advanced settings forms | [`config_flow.py`](custom_components/flaktgroup/config_flow.py) |
| Register map and Modbus transport | [`const.py`](custom_components/flaktgroup/const.py), [`modbus_coordinator.py`](custom_components/flaktgroup/modbus_coordinator.py) |
| English UI messages | [`translations/en.json`](custom_components/flaktgroup/translations/en.json) |
| Home Assistant and Modbus regression tests | [`tests/`](tests/) |

When changing a config flow, test both the flow result and Home Assistant’s frontend schema serialization. When changing register behavior, document the source for the address, scale, or range and test the behavior using mocked Modbus responses.

## Test on an RDKS

Use a test Home Assistant instance with network access to the unit, or back up the existing installation first. Install the branch using the [manual installation steps](README.md#manual-installation).

1. Add the device and compare the preset, setpoint, and a few temperatures with the controller. On upgrade, check that existing entity IDs still resolve.
2. Open **Configure** and verify that the current settings appear.
3. Record an existing setting. Change it within the normal range, confirm the new value at the controller, then restore the original value.
4. Briefly disconnect Modbus networking with the unit still powered. Confirm that Home Assistant reports unavailability and resumes readings after reconnecting.

Report which checks ran against hardware in the pull request.

## Prepare a Marketplace release

1. Run the local checks and the hardware smoke test. Ensure the GitHub Actions for tests, hassfest, and Marketplace validation pass.
2. Match the integration manifest version to the release tag. Update the Marketplace minimum in `hacs.json` when the compatibility floor changes.
3. On first publication, make the GitHub repository public, enable Issues, add a description and topics, and point the manifest documentation and issue links at GitHub.
4. Prepare a GitHub release draft with user-facing changes and any upgrade steps. Publish it after validation. Marketplace can install the integration from the tagged repository layout.
5. Verify installation through **Settings → Marketplace → Add from link**. Submit the repository to the catalog when ready. [Marketplace catalog guide](https://contributors.home-assistant.io/marketplace/guides/catalog/)

## Source history

The RDKS integration comes from the `flaktgroup_integration_all` branch of the Home Assistant Core fork. These are the original integration commits, in order.

- `2bca964f0a71e153e3fc1827aac7904d3741d654`
- `c8eb81e1a17213824b53d4492fe1398cfaafb230`
- `e3dff10a1b8d03ab0bdf10e2dacc93e869fa7ecf`
- `3bd61c41ca41c2bb36e3f6e3f89e0918b8d059af`
- `e4a9844bd702e7c8d307d4cf5c5498dacebd553d`
- `6e753a6ea59dc1ba1ffdf70ba57e4c12a2c90cb7`
- `8d9ea7363f23d12e5d5722ca0639d77ddad479da`
