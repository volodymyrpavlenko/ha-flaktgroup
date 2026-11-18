# FläktGroup integration

Target Home Assistant 2026.11.2 and Python 3.14. The supported hardware is FläktGroup RDKS over Modbus TCP.

Keep the Marketplace package under `custom_components/flaktgroup`. Preserve entity registry identity and existing configuration when upgrading. Keep all network I/O asynchronous and serialized per connection.

Treat the imported register map as the compatibility baseline. Document evidence for changes to addresses, scaling, and writable ranges. Use mocked Modbus traffic in automated tests. Before a release, verify readings, a reversible control change, and recovery after disconnect on an RDKS unit.

Run the README's test and Ruff commands before sharing changes. Keep the manifest version aligned with the release tag and run hassfest and Marketplace validation before publishing.
