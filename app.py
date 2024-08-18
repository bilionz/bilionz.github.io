from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random key


# Paths for persistent storage
DATA_DIR = '/mnt/data'
TEAM_CONFIG_PATH = os.path.join(DATA_DIR, 'team_config.json')
SOLVED_RIDDLES_PATH = os.path.join(DATA_DIR, 'solved_riddles.json')

RIDDLE_PATHS_PATH = os.path.join(DATA_DIR, 'riddle_paths.json')

# Flag to determine whether to replace existing data on deploy
REPLACE_ON_DEPLOY = False

# Initialize data storage
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return default

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Load riddles configuration
riddles_config = load_json('riddles.json', [])

riddle_paths = load_json(RIDDLE_PATHS_PATH, {})

# Load or initialize team configuration
if REPLACE_ON_DEPLOY or not os.path.exists(TEAM_CONFIG_PATH):
    team_config = {"teams": []}
    save_json(TEAM_CONFIG_PATH, team_config)
else:
    team_config = load_json(TEAM_CONFIG_PATH, {"teams": []})

teams = team_config['teams']

# Load or initialize solved riddles
if REPLACE_ON_DEPLOY or not os.path.exists(SOLVED_RIDDLES_PATH):
    solved_riddles = {}
    save_json(SOLVED_RIDDLES_PATH, solved_riddles)
else:
    solved_riddles = load_json(SOLVED_RIDDLES_PATH, {})

@app.route('/')
def index():
    if 'team_name' in session:
        return render_template('index.html', team_name=session['team_name'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        team_name = request.form.get('teamName')

        if not any(team['team_name'] == team_name for team in teams):
            return render_template('login.html', error='Invalid team name.')

        session['team_name'] = team_name
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('team_name', None)
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_team', methods=['POST'])
def register_team():
    data = request.json
    team_name = data.get('teamName')
    riddle_path_id = data.get('riddlePathId')

    if not team_name or not riddle_path_id:
        return jsonify({'success': False, 'error': 'All fields are required.'})

    if any(team['team_name'] == team_name for team in teams):
        return jsonify({'success': False, 'error': 'Team name already exists.'})

    new_team = {
        'team_name': team_name,
        'infected_members': [],
        'riddle_path_id': riddle_path_id,
        'current_riddle_index': 0
    }
    teams.append(new_team)
    save_json(TEAM_CONFIG_PATH, {'teams': teams})

    return jsonify({'success': True, 'message': 'Team registered successfully!'})



@app.route('/riddle_s')
def riddle_s():
    if 'team_name' not in session:
        return redirect(url_for('login'))

    auto_player = request.args.get('auto_player')
    if auto_player:
        team_name = session['team_name']
        team = next((team for team in teams if team['team_name'] == team_name), None)

        if team and auto_player not in team['infected_members']:
            team['infected_members'].append(auto_player)
            save_json(TEAM_CONFIG_PATH, {'teams': teams})

    return render_template('riddle_s.html')

@app.route('/add_infected', methods=['POST'])
def add_infected():
    if 'team_name' not in session:
        return jsonify({'success': False, 'error': 'Not logged in.'})

    data = request.json
    team_name = session['team_name']
    player_name = data.get('playerName')

    if not player_name:
        return jsonify({'success': False, 'error': 'Player name is required.'})

    team = next((team for team in teams if team['team_name'] == team_name), None)

    if not team:
        return jsonify({'success': False, 'error': 'Team does not exist.'})

    if player_name in team['infected_members']:
        return jsonify({'success': False, 'error': 'Player is already infected.'})

    team['infected_members'].append(player_name)
    save_json(TEAM_CONFIG_PATH, {'teams': teams})

    return jsonify({'success': True, 'message': f'{player_name} added to infected members of {team_name}.'})

@app.route('/solve', methods=['POST'])
def solve_riddle():
    if 'team_name' not in session:
        return jsonify({'success': False, 'error': 'Not logged in.'})

    data = request.json
    team_name = session['team_name']
    riddle_id = data.get('riddleId')
    solution = data.get('solution')

    team = next((t for t in teams if t['team_name'] == team_name), None)

    if not team:
        return jsonify({'success': False, 'error': 'Invalid team name.'})

    riddle_path_id = team['riddle_path_id']
    riddle_paths = load_json('riddle_paths.json', {})
    current_path = riddle_paths.get(riddle_path_id, [])

    if team['current_riddle_index'] >= len(current_path):
        return jsonify({'success': False, 'error': 'No more riddles in path.'})

    current_riddle_id = current_path[team['current_riddle_index']]
    current_riddle = next((r for r in riddles_config if r['id'] == current_riddle_id), None)

    if not current_riddle or current_riddle['answer'] != solution:
        return jsonify({'success': False, 'error': 'Incorrect solution.'})

    # Move to the next riddle
    team['current_riddle_index'] += 1
    save_json(TEAM_CONFIG_PATH, {'teams': teams})

    if team['current_riddle_index'] < len(current_path):
        next_riddle_id = current_path[team['current_riddle_index']]
        next_riddle = next((r for r in riddles_config if r['id'] == next_riddle_id), None)
        return jsonify({'success': True, 'narrative': next_riddle['narrative']})
    else:
        return jsonify({'success': True, 'narrative': 'Congratulations! You have completed the path.'})

@app.route('/solved')
def solved():
    return render_template('solved.html', teams=teams, solved_riddles=solved_riddles)

@app.route('/get_team_data')
def get_team_data():
    return jsonify(teams)

@app.route('/get_solved_riddles')
def get_solved_riddles():
    return jsonify(solved_riddles)

if __name__ == '__main__':
    app.run(debug=True)
