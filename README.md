# smartmeter_faker

This project now doubles as a Home Assistant add-on for exposing Home Assistant sensor data as a fake Modbus TCP EM420-style meter.

For Home Assistant add-on usage, see [DOCS.md](/Users/fredriklilja/Development/smartmeter_faker/DOCS.md). The add-on uses the internal Home Assistant API proxy by default, so URL and token are no longer exposed as add-on options.

`modbus_bridge.py` still supports standalone usage and reads Home Assistant settings from environment variables first, with YAML as an optional fallback.

1. For Docker or Compose, copy `.env.example` to `.env` and set the `HA_*` variables.
2. For local file-based config, copy [homeassistant.yaml.example](/Users/fredriklilja/Development/smartmeter_faker/homeassistant.yaml.example) to `homeassistant.yaml`.
3. Start the bridge with `python3 modbus_bridge.py` or pass `--config /path/to/file.yaml`.

Environment variables take precedence over YAML. `HA_TOKEN_FILE` is also supported for Docker/Kubernetes secret mounts.

## GitHub Actions

[`python-build.yml`](/Users/fredriklilja/Development/smartmeter_faker/.github/workflows/python-build.yml) installs the pinned dependencies from [`requirements.txt`](/Users/fredriklilja/Development/smartmeter_faker/requirements.txt) and verifies that `modbus_bridge.py` compiles on every push to `main` and on pull requests.

[`docker-build.yml`](/Users/fredriklilja/Development/smartmeter_faker/.github/workflows/docker-build.yml) builds a multi-architecture Docker image for `linux/amd64`, `linux/arm64`, `linux/arm/v7`, and `linux/arm/v6`. On pushes to `main`, including merged pull requests, it publishes to both `ghcr.io/<owner>/smartmeter-modbus-bridge` and Docker Hub as `<DOCKERHUB_USERNAME>/smartmeter-modbus-bridge` with the `edge` tag. On `v*` tags, it publishes release images with the `latest` tag. On pull requests, it only validates that the multi-arch build succeeds. Manual runs from the Actions tab can publish to GHCR, Docker Hub, or both by selecting the workflow inputs.

Set these GitHub repository secrets for Docker Hub publishing:

1. `DOCKERHUB_USERNAME`
2. `DOCKERHUB_TOKEN`

For a manual Docker Hub publish in GitHub Actions, open `Docker Build`, click `Run workflow`, set `publish_to_dockerhub` to `true`, and choose the `image_tag` you want to publish.

## Home Assistant Add-on

This repository root is now a single add-on folder and can be copied directly into Home Assistant's local add-ons directory, for example `/addons/smartmeter_faker`.

The add-on manifest is in [config.yaml](/Users/fredriklilja/Development/smartmeter_faker/config.yaml), the build settings are in [build.yaml](/Users/fredriklilja/Development/smartmeter_faker/build.yaml), and startup is handled by [run.sh](/Users/fredriklilja/Development/smartmeter_faker/run.sh).

## Docker

Build the container locally with `docker build -t smartmeter-modbus-bridge .`.

The image includes a Docker `HEALTHCHECK` that reports unhealthy if the bridge has not completed a successful Home Assistant refresh within the configured age window. The application also logs its version on startup, and `python3 modbus_bridge.py --version` prints the current version string.

Runtime logs are emitted as JSON and include structured events for Home Assistant poll success/failure, Modbus reads, and server lifecycle. Home Assistant polling now uses exponential backoff after failures, capped by `--max-backoff`.

Run it directly with environment variables:

```sh
docker run --rm \
  -p 5020:5020 \
  --env-file .env \
  frli4797/smartmeter-modbus-bridge:latest
```

## Docker Compose

Use [`compose.yaml`](/Users/fredriklilja/Development/smartmeter_faker/compose.yaml) together with a local `.env` file:

```sh
cp .env.example .env
docker compose up -d
```
