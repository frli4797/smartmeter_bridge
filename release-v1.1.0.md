# Release Title

`v1.1.0` improve Home Assistant startup retries and prepare meter mapping extensibility.

## Highlights

- Treat temporary Home Assistant connectivity failures during startup or host reboot as expected for a configurable grace period.
- Add `startup_grace` so add-on users can tune how long startup connectivity failures stay in the quieter retry flow.
- Introduce a meter register mapper abstraction around the EM420 layout to make future meter layouts easier to add.

## What's New

### Features

- Added `startup_grace`, defaulting to `120` seconds, to control the startup/reboot retry grace period.
- Added a meter register mapper interface with the existing EM420 register layout implemented through it.

### Fixes and Improvements

- Initial Home Assistant connectivity failures are now retried with backoff instead of being treated as immediate startup failures.
- Startup retry logs are quieter during the grace period and escalate if failures persist.
- Recovery logs now include outage and suppressed-failure context.

### CI/CD and Tooling

- Added tests for startup failure logging, persistent failure escalation, recovery logging, and the meter mapper update path.
- Added repository agent instructions for branch hygiene, test expectations, release workflow, and delivery notes.
- Removed a tracked macOS `.DS_Store` file and ignored future `.DS_Store` files.

## Upgrade Notes

- Upgrade normally to `v1.1.0`.
- Verify the add-on version shows `1.1.0` after upgrading.
- The new `startup_grace` option defaults to `120` seconds. Most installations can keep the default.
- If Home Assistant often takes longer than two minutes to become reachable after reboot, increase `startup_grace`.

## Notes

- This is a minor release because it adds a new user-facing configuration option and changes startup retry behavior.

## Full Changelog

- Compare: `v1.0.12...v1.1.0`
