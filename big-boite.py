import urllib.request
from flask import Flask, render_template, request, redirect, url_for, session, send_file, Response, Request, stream_with_context
#from flask_socketio import SocketIO, emit
import os
import json
import argparse
import subprocess
import base64
import time

from c285_py.api import Api

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
#socketio = SocketIO(app)

SCREENSHOT_PATH = "/tmp/output.png"

#
# Argument parsing
#

parser = argparse.ArgumentParser(description='big boîte - a (very barebones) web interface for the AVerMedia Game Capture HD II (C285)')
parser.add_argument('ip', type=str, help='C285 IP address')
parser.add_argument('--port', type=int, nargs='?', default="5000", help='Port to run the application on')
args = parser.parse_args()

def is_ffmpeg_installed():
    try:
        # Run the ffmpeg command with the help option
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    
def get_files():
    api = Api(args.ip)
    api.pairing()
    api.get_files_infos("/media/sda1/")
    time.sleep(0.1)
    response = api.files_infos_get()

    if "files_infos" not in response:
        return None

    # cut off parent path
    # sort by newest
    files = response["files_infos"][1:]
    files.reverse()

    return files

@app.route('/', methods=['GET', 'POST'])
@app.route('/latest', methods=['GET', 'POST'])
def latest():
    recent_file = None

    hdd_files = get_files()
    if hdd_files is not None:
        if len(hdd_files) > 0:
            recent_file = hdd_files[0]

    for hdd_file in hdd_files:
        start_index = hdd_file["thumb_position"].index(".thumb")
        hdd_file["thumb_position_truncated"] = hdd_file["thumb_position"][start_index + 7:]

    return render_template('latest.html', recent_file=recent_file)

@app.route('/latest_screenshot', methods=['GET'])
def latest_screenshot():
    recent_file = None

    hdd_files = get_files()
    if hdd_files is not None:
        if len(hdd_files) > 0:
            recent_file = hdd_files[0]

    api = Api(args.ip)
    screenshot = api.get_file_content(f"/media/sda1/{recent_file['file_name']}")

    return Response(screenshot, content_type="image/jpeg")

@app.route('/screenshot/<string:filename>', methods=['GET'])
def screenshot(filename, headers={}):
    if filename[-3:] != "jpg":
        return "Requested file is not a valid path"

    api = Api(args.ip)
    screenshot = api.get_file_content(f"/media/sda1/{filename}")

    return Response(screenshot, content_type="image/jpeg", headers=headers)

@app.route('/screenshot/<string:filename>/download', methods=['GET'])
def download_screenshot(filename):
    return screenshot(filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.route('/thumb/<string:filename>', methods=['GET'])
def thumb(filename):
    return screenshot(f".thumb/{filename}")

# TODO: update c285_py to deduplicate some code
@app.route('/stream/<string:filename>', methods=['GET'])
def stream(filename):
    api = Api(args.ip)
    api.pairing()

    local_path_encoded = urllib.parse.quote_plus(f"/media/sda1/{filename}")
    target_url = f"http://{args.ip}:24170/eos/method/get_file_content/content_name={local_path_encoded}"

    # Open the video URL as a stream
    request = urllib.request.Request(target_url)
    remote_response = urllib.request.urlopen(request)

    content_type = remote_response.headers.get("Content-Type", "application/octet-stream")

    # Stream the data to the client as it is received
    def generate():
        while True:
            chunk = remote_response.read(8192)  # Read in chunks of 8KB
            if not chunk:
                break
            yield chunk

    # Return the response as a stream with the same content-type
    return Response(
        stream_with_context(generate()),
        content_type=remote_response.headers.get("Content-Type", content_type)
    )

if __name__ == '__main__':
    app.run(debug=True, port=args.port, host="0.0.0.0")