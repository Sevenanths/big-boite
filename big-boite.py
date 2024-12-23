from flask import Flask, render_template, request, redirect, url_for, session, send_file
#from flask_socketio import SocketIO, emit
import os
import json
import argparse
import subprocess
import base64

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
#socketio = SocketIO(app)

SCREENSHOT_PATH = "/tmp/output.png"

#
# Argument parsing
#

parser = argparse.ArgumentParser(description='big boîte - a (very barebones) web interface for the AVerMedia Game Capture HD II (C285)')
parser.add_argument('mode', type=str, help='mode - live or test')
parser.add_argument('--port', type=int, nargs='?', default="5000", help='Port to run the application on')
args = parser.parse_args()

def is_ffmpeg_installed():
    try:
        # Run the ffmpeg command with the help option
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@app.route('/', methods=['GET', 'POST'])
def welcome():
    return render_template('welcome.html')

@app.route('/latest_screenshot', methods=['GET'])
def latest_screenshot():
    return send_file(SCREENSHOT_PATH, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=args.port, host="0.0.0.0")