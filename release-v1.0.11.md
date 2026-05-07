# Release Title

`v1.0.11` harden Modbus serving when Home Assistant data is unavailable.

## Highlights

- Stop serving Modbus register data when required Home Assistant entities are unavailable, unknown, empty, or non-numeric.
- Resume Modbus serving automatically after Home Assistant data recovers.
- Add an option to calculate total power factor from total power plus per-phase voltage and current sensors.

## What's New

### Features

- Added `calculate_power_factor` so the bridge can derive total power factor when no dedicated Home Assistant power factor entity is available.
- Allow `total_pf` to be omitted when calculated power factor mode is enabled.

### Fixes and Improvements

- Required Home Assistant readings are now handled strictly for register updates: zero remains valid, but unavailable or invalid states stop the poll.
- Modbus reads are blocked until the bridge has completed a successful Home Assistant poll with valid required data.
- Modbus reads resume after a later successful Home Assistant poll, without requiring an add-on restart.
- Phase-derived total power behavior has been simplified around the calculated power factor flow.

### CI/CD and Tooling

- Added regression coverage for zero-valued readings, unavailable entity handling, and recovery after Home Assistant entities become available again.
- Added test coverage for the calculated power factor configuration path.

## Upgrade Notes

- Upgrade normally to `v1.0.11`.
- Verify the add-on version shows `1.0.11` after upgrading.
- If you enable `calculate_power_factor`, `total_pf` can be left empty; otherwise keep `total_pf` configured as before.
- If a required Home Assistant sensor becomes unavailable, Modbus clients will stop receiving meter data until the sensor returns to a numeric state.

## Notes

- This release focuses on data correctness and avoiding misleading fallback values on the Modbus interface.

## Full Changelog

- Compare: `v1.0.10...v1.0.11`
