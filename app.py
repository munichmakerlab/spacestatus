import base64
import requests
import re
from flask import Flask, request, jsonify, render_template, current_app
from flask_mqtt import Mqtt
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

app.config['MQTT_BROKER_URL'] = 'mqtt.munichmakerlab.de'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True

topic = 'mumalab/room/status'

mqtt_client = Mqtt(app)

space_status = -1

json_headers = {
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'no-cache, must-revalidate',
    'Expires': 'Mon, 19 Jul 1997 00:00:00 GMT'
}

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe(topic) # subscribe topic
    else:
        print('Bad connection. Code:', rc)


@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    global space_status
    
    print(f'Received message on topic: {message.topic} with payload: {message.payload.decode()}')
    space_status = message.payload.decode()
    
@app.route("/")
def index():
    return render_template('index.html', status=space_status, devices=get_devices())

@app.route("/simple.php")
@app.route("/api/v2/simple.txt")
def get_status_text():
    if space_status == "1":
        return "open"
    elif space_status == "0":
        return "closed"
    else:
        return "unknown"

@app.route('/api.php')
@app.route('/api/v2/status.json')
def get_status_api():
    data = {
        "door": get_status_text()
    }

    return jsonify(data), json_headers

@app.route('/image.php')
@app.route('/api/v2/image.png')
def send_status_image():
    if space_status == "1":
        filename = "open.png"
    elif space_status == "0":
        filename = "closed.png"
    else:
        filename = "unknown.png"
    
    return current_app.send_static_file(filename)

@app.route('/spaceapi.json')
def get_space_api():
    data = {
        "api": "0.13",
        "space": "Munich Maker Lab",
        "logo": "https://wiki.munichmakerlab.de/images/mumalab.png",
        "url": "https://munichmakerlab.de/",
        "location": {
            "address": "Dachauer Str. 112h, 80636 München, Germany",
            "lon": 11.5482333,
            "lat": 48.158752
        },
        "spacefed": {
            "spacenet": False,
            "spacesaml": False,
            "spacephone": False
        },
        "contact": {
            "email": "info@munichmakerlab.de",
            "irc": "irc://irc.hackint.eu/munichmakerlab",
            "ml": "discuss@munichmakerlab.de",
            "twitter": "@munichmakerlab",
            "phone": "+498921553954",
            "issue_mail": base64.b64encode("spaceapi@tiefpunkt.com".encode()).decode()
        },
        "issue_report_channels": ["issue_mail"],
        "feeds": {
            "log": {
                "type": "application/rss+xml",
                "url": "http://log.munichmakerlab.de/rss"
            },
            "calendar": {
                "type": "text/calendar",
                "url": "https://calendar.google.com/calendar/ical/lbd0aa2rlahecp7juvp35hd0k0%40group.calendar.google.com/public/basic.ics"
            }
        },
        "cache": {"schedule": "m.02"},
        "state": {
            "open": (space_status == '1')
        },
        "projects": [
            "https://github.com/munichmakerlab",
            "https://munichmakerlab.de/wiki/Category:Project"
        ]
    }

    return jsonify(data), json_headers

def get_device_status(device):
    url = f"https://wiki.munichmakerlab.de/index.php?title={device}&action=edit"
    response = requests.get(url)
    raw = response.text
    matches = re.findall(r'\{\{(ThingInfoBox|project)(.+?)\}\}', raw, re.DOTALL)
    result = []
    for match in matches:
        entry = match[1]
        res = {}
        for line in entry.split('\n'):
            if '=' not in line:
                continue
            line = line.strip().replace('|', '')
            key, value = map(str.strip, line.split('=', 1))
            res[key] = value
        result.append(res)
    return result

@cache.cached(timeout=300, key_prefix="devices")
def get_devices():
    data = {}
    names = {
        "Lusa": "Lusa (3D printer)",
        "Rusa": "Rusa (3D printer)",
        "LaserCutter": "Laser Cutter",
        "CNC Mill": "CNC Mill",
    }

    for device in ['Prusa_Mini', 'LaserCutter', 'CNC_router_build']:
        for entry in get_device_status(device):
            if 'name' in entry and entry['name'] in names:
                data[names[entry['name']]] = entry.get("status", "")

    return data

@app.route("/api/v2/devices.json")
def get_devices_api():
    return jsonify(get_devices()), json_headers

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)