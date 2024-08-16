from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

app = Flask(__name__)

# Load config and solved riddles
with open('config.json') as config_file:
    riddles_config = json.load(config_file)

def load_solved_riddles():
    try:
        with open('solved_riddles.json') as solved_file:
            return json.load(solved_file)
    except FileNotFoundError:
        return {}

def save_solved_riddles(solved_riddles):
    with open('solved_riddles.json', 'w') as solved_file:
        json.dump(solved_riddles, solved_file, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/decode', methods=['POST'])
def decode_riddle():
    data = request.json
    team_name = data.get('teamName')
    riddle_id = data.get('riddleId')
    solution = data.get('solution')

    solved_riddles = load_solved_riddles()

    if riddle_id not in riddles_config:
        return jsonify({'success': False, 'error': 'Invalid riddle ID.'})

    if riddles_config[riddle_id] != solution:
        return jsonify({'success': False, 'error': 'Incorrect solution.'})

    if team_name not in solved_riddles:
        solved_riddles[team_name] = {}

    if riddle_id in solved_riddles[team_name]:
        return jsonify({'success': False, 'error': 'Riddle already solved.'})

    solved_riddles[team_name][riddle_id] = datetime.now().isoformat()
    save_solved_riddles(solved_riddles)

    return jsonify({'success': True, 'message': 'Riddle solved successfully!'})

if __name__ == '__main__':
    app.run(debug=True)
