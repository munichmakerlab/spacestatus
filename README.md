# MunichMakerLab Space Status Frontend

This is the updated version https://status.munichmakerlab.de, wrapped in an easy flask app, runnable as a docker container.

It also handles our spaceAPI endpoint (https://status.munichmakerlab.de/spaceapi.json)

## Development
```bash
uv sync
uv run python app.py
```

## Docker
```bash
docker compose up --build
```
Images are published to `ghcr.io/munichmakerlab/spacestatus` on every version tag push (e.g. `v1.0.0`), tagged as `latest`, `<major>.<minor>.<patch>`, `<major>.<minor>` and `<major>`.

## CI
* `lint.yml` — ruff + hadolint on every push/PR.
* `docker-build-push.yml` — builds & pushes the image to GHCR on tag pushes.

## Notes
* We run gunicorn with a single worker because of Flask-MQTT limitations.
