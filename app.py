from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

app = Flask(__name__)

# Load riddles configuration
with open('config.json') as config_file:
    riddles_config = json.load(config_file)

# Load team configuration
def load_team_config():
    try:
        with open('team_config.json') as team_config_file:
            return json.load(team_config_file)
    except FileNotFoundError:
        return {"teams": []}

def save_team_config(team_config):
    with open('team_config.json', 'w') as team_config_file:
        json.dump(team_config, team_config_file, indent=4)

team_config = load_team_config()
teams = team_config['teams']

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

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_team', methods=['POST'])
def register_team():
    data = request.json
    team_name = data.get('teamName')
    infected_member = data.get('infectedMember')

    if not team_name or not infected_member:
        return jsonify({'success': False, 'error': 'All fields are required.'})

    if any(team['team_name'] == team_name for team in teams):
        return jsonify({'success': False, 'error': 'Team name already exists.'})

    new_team = {
        'team_name': team_name,
        'infected_member': infected_member
    }
    teams.append(new_team)
    save_team_config({'teams': teams})

    return jsonify({'success': True, 'message': 'Team registered successfully!'})

@app.route('/solve', methods=['POST'])
def solve_riddle():
    data = request.json
    team_name = data.get('teamName')
    riddle_id = data.get('riddleId')
    riddle_part = data.get('riddlePart')
    solution = data.get('solution')

    # Check if the team name is valid
    if not any(team['team_name'] == team_name for team in teams):
        return jsonify({'success': False, 'error': 'Invalid team name.'})

    solved_riddles = load_solved_riddles()

    riddle = next((r for r in riddles_config if r['riddleid'] == riddle_id and r['part'] == riddle_part), None)

    if not riddle:
        return jsonify({'success': False, 'error': 'Invalid riddle ID or part.'})

    if riddle['solution'] != solution:
        return jsonify({'success': False, 'error': 'Incorrect solution.'})

    if team_name not in solved_riddles:
        solved_riddles[team_name] = {}

    if riddle_id not in solved_riddles[team_name]:
        solved_riddles[team_name][riddle_id] = {}

    if riddle_part in solved_riddles[team_name][riddle_id]:
        # return jsonify({'success': False, 'error': 'Riddle part already solved.'})
        
        return jsonify({
            'success': True,
            'resolution': riddle['resolution'],
            'image': riddle.get('image', None)
        })

    solved_riddles[team_name][riddle_id][riddle_part] = datetime.now().isoformat()
    save_solved_riddles(solved_riddles)

    return jsonify({
        'success': True,
        'resolution': riddle['resolution'],
        'image': riddle.get('image', None)
    })

@app.route('/solved')
def solved():
    return render_template('solved.html', teams=teams)

@app.route('/get_solved_riddles')
def get_solved_riddles():
    return jsonify(load_solved_riddles())

if __name__ == '__main__':
    app.run(debug=True)
