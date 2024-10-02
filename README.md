# MunichMakerLab Space Status Frontend

This is the updated version https://status.munichmakerlab.de, wrapped in an easy flask app, runnable as a docker container.

It also handles our spaceAPI endpoint (https://status.munichmakerlab.de/spaceapi.json)

## Notes
* We run gunicorn with a single worker because of Flask-MQTT limitations.