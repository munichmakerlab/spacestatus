# MunichMakerLab Space Status Frontend

This is the updated version https://status.munichmakerlab.de, wrapped in an easy flask app, runnable as a docker container.

It also handles our spaceAPI endpoint (https://status.munichmakerlab.de/spaceapi.json)

## Development
```bash
uv sync
uv run python app.py
```

## Configuration
All settings have sensible defaults and are only needed if you deviate from the MunichMakerLab setup. Set them as environment variables (e.g. via `docker run -e` or `compose.yml`'s `environment:`).

| Variable | Default | Description |
| --- | --- | --- |
| `MQTT_BROKER_URL` | `mqtt.munichmakerlab.de` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | `""` | MQTT username (if the broker requires auth) |
| `MQTT_PASSWORD` | `""` | MQTT password (if the broker requires auth) |
| `MQTT_KEEPALIVE` | `5` | MQTT keepalive interval in seconds |
| `MQTT_TLS_ENABLED` | `false` | Set to `true` if the broker requires TLS |
| `MQTT_TOPIC` | `mumalab/room/status` | MQTT topic the door status is published on |
| `GRAFANA_DASHBOARD_UID` | `6ce9eabaea5141a3b4fa1aaad98e45b9` | UID of the public Grafana dashboard used for the opening-times heatmap |
| `GRAFANA_PANEL_ID` | `1` | ID of the panel within that dashboard |
| `HEATMAP_REFRESH_INTERVAL` | `259200` (3 days) | How often (in seconds) the heatmap data is refreshed in the background |

## Docker
```bash
docker compose up --build
```
Images are published to `ghcr.io/munichmakerlab/spacestatus`:
* every push to `main` → `main` tag
* every version tag push (e.g. `v1.0.0`) → `latest`, `<major>.<minor>.<patch>`, `<major>.<minor>` and `<major>`

## CI
* `lint.yml` — ruff + hadolint on every push/PR.
* `docker-build-push.yml` — builds & pushes the image to GHCR on push to `main` and on version tag pushes.

## Notes
* We run gunicorn with a single worker because of Flask-MQTT limitations.
