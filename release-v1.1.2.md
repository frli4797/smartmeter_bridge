# Release Title

`v1.1.2` fix VictoriaLogs message field compatibility.

## Highlights

- Emit the VictoriaLogs `_msg` field in structured JSON logs so log ingestion no longer reports missing message fields.
- Keep the existing `message` field for compatibility with existing dashboards, searches, and log tooling.
- Add regression coverage for the structured log payload shape.

## What's New

### Features

- No new user-facing features in this release.

### Fixes and Improvements

- Structured logs now include `_msg` alongside `message`, matching VictoriaLogs' required message field while preserving the previous field name.
- Home Assistant polling heartbeat logs and other add-on log events should no longer be ingested as VictoriaLogs errors for a missing `_msg` field.

### CI/CD and Tooling

- Added a formatter regression test to verify release logs include both `_msg` and `message`.

## Upgrade Notes

- Upgrade normally to `v1.1.2`.
- Verify the add-on version shows `1.1.2` after upgrading.
- No configuration changes are required.

## Notes

- This is a patch release focused on structured logging compatibility with VictoriaLogs.

## Full Changelog

- Compare: `v1.1.1...v1.1.2`
