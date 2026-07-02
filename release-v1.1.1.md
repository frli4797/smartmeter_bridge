# Release Title

`v1.1.1` keep Modbus reads available during startup errors and improve Docker build caching.

## Highlights

- Keep serving Modbus read requests during startup retry periods when Home Assistant data is not available yet.
- Prevent version-only Docker builds from invalidating the dependency install layer.
- Add BuildKit pip cache mounts so dependency downloads are reused when the dependency layer must rebuild.

## What's New

### Features

- No new user-facing features in this release.

### Fixes and Improvements

- Modbus reads during startup Home Assistant errors now return the bridge's current fallback register values instead of failing the read path.
- The standalone and add-on Dockerfiles now place `APP_VERSION` after dependency installation so build version changes do not force dependency reinstalls.
- Docker dependency installs now use BuildKit cache mounts for pip downloads.

### CI/CD and Tooling

- The Docker publishing workflow now uses an explicit GitHub Actions cache scope for the standalone image.
- Local Buildx verification confirmed repeated builds cache the dependency install layer, including when `BUILD_VERSION` changes.

## Upgrade Notes

- Upgrade normally to `v1.1.1`.
- Verify the add-on version shows `1.1.1` after upgrading.
- No configuration changes are required.

## Notes

- This is a patch release focused on startup resilience and build performance.

## Full Changelog

- Compare: `v1.1.0...v1.1.1`
