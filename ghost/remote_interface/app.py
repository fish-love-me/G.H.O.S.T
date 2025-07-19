import sys
import os
# הוספת הנתיב לתיקיית ghost (שמכילה את modules)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, render_template, jsonify
from modules.handle_remote_input import handle_remote_input  # זה צריך לעבוד עכשיו


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_text', methods=['POST'])
def send_text():
    text = request.form.get('text')
    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    result = handle_remote_input(text)
    return jsonify({"status": "ok", "response": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
