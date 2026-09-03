import base64
import os
import re
import threading
import time

import requests
from flask import Flask, current_app, jsonify, render_template
from flask_caching import Cache
from flask_mqtt import Mqtt


def _env_str(name, default):
    return os.environ.get(name, default)


def _env_int(name, default):
    value = os.environ.get(name)
    return int(value) if value else default


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

app.config['MQTT_BROKER_URL'] = _env_str('MQTT_BROKER_URL', 'mqtt.munichmakerlab.de')
app.config['MQTT_BROKER_PORT'] = _env_int('MQTT_BROKER_PORT', 1883)
app.config['MQTT_USERNAME'] = _env_str('MQTT_USERNAME', '')
app.config['MQTT_PASSWORD'] = _env_str('MQTT_PASSWORD', '')
app.config['MQTT_KEEPALIVE'] = _env_int('MQTT_KEEPALIVE', 5)
app.config['MQTT_TLS_ENABLED'] = _env_bool('MQTT_TLS_ENABLED', False)

topic = _env_str('MQTT_TOPIC', 'mumalab/room/status')

GRAFANA_DASHBOARD_UID = _env_str('GRAFANA_DASHBOARD_UID', "6ce9eabaea5141a3b4fa1aaad98e45b9")
GRAFANA_PANEL_ID = _env_int('GRAFANA_PANEL_ID', 1)
WEEKDAY_FIELD_ORDER = ["1", "2", "3", "4", "5", "6", "7"]  # Mon..Sun
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HEATMAP_CACHE_KEY = "opening_heatmap"
HEATMAP_REFRESH_INTERVAL = _env_int('HEATMAP_REFRESH_INTERVAL', 259200)  # seconds; every 3 days by default

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
    
def _fetch_opening_heatmap():
    url = f"https://monitoring.munichmakerlab.de/api/public/dashboards/{GRAFANA_DASHBOARD_UID}/panels/{GRAFANA_PANEL_ID}/query"
    payload = {"intervalMs": 3600000, "maxDataPoints": 1000, "timeRange": {"from": "now-30d", "to": "now"}}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        frame = response.json()["results"]["A"]["frames"][0]
        fields = frame["schema"]["fields"]
        values = frame["data"]["values"]
        field_index = {f["name"]: i for i, f in enumerate(fields)}
        hours = values[field_index["hour"]]
        rows = []
        for row_idx, hour in enumerate(hours):
            row = [values[field_index[day]][row_idx] for day in WEEKDAY_FIELD_ORDER]
            rows.append({"hour": hour, "cells": row})
        return {"weekdays": WEEKDAY_LABELS, "rows": rows}
    except Exception:
        return None

HEATMAP_RETRY_INTERVAL = 30  # seconds; retry quickly after a failed fetch instead of waiting a full cycle

def _fetch_and_cache_opening_heatmap():
    data = _fetch_opening_heatmap()
    if data is not None:
        cache.set(HEATMAP_CACHE_KEY, data, timeout=HEATMAP_REFRESH_INTERVAL * 2)
    return data

def _refresh_opening_heatmap_loop(last_fetch_succeeded):
    success = last_fetch_succeeded
    while True:
        time.sleep(HEATMAP_REFRESH_INTERVAL if success else HEATMAP_RETRY_INTERVAL)
        success = _fetch_and_cache_opening_heatmap() is not None

def get_opening_heatmap():
    return cache.get(HEATMAP_CACHE_KEY)

# Fetch once synchronously so the data is available immediately after a restart,
# then hand off to a background thread for the periodic refresh.
_initial_heatmap_fetch_succeeded = _fetch_and_cache_opening_heatmap() is not None
threading.Thread(target=_refresh_opening_heatmap_loop, args=(_initial_heatmap_fetch_succeeded,), daemon=True).start()

@app.template_filter('heatmap_color')
def heatmap_color(value):
    if value is None:
        return "#2D333B"
    if value >= 0.8:
        return "#1F6F3F"
    if value >= 0.5:
        return "#7A5C00"
    return "#30363D"

@app.route("/")
def index():
    return render_template('index.html', status=space_status, devices=get_devices(), heatmap=get_opening_heatmap())

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