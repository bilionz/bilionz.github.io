from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random key

# Load riddles configuration
with open('config.json') as config_file:
    riddles_config = json.load(config_file)

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
            save_team_config({'teams': teams})

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
    save_team_config({'teams': teams})

    return jsonify({'success': True, 'message': f'{player_name} added to infected members of {team_name}.'})

@app.route('/solve', methods=['POST'])
def solve_riddle():
    if 'team_name' not in session:
        return jsonify({'success': False, 'error': 'Not logged in.'})

    data = request.json
    team_name = session['team_name']
    riddle_id = data.get('riddleId')
    riddle_part = data.get('riddlePart')
    solution = data.get('solution')

    team = next((t for t in teams if t['team_name'] == team_name), None)

    if not team:
        return jsonify({'success': False, 'error': 'Invalid team name.'})

    team['attempts'] += 1
    save_team_config({'teams': teams})

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
        return jsonify({'success': False, 'error': 'Riddle part already solved.'})

    solved_riddles[team_name][riddle_id][riddle_part] = datetime.now().isoformat()
    save_solved_riddles(solved_riddles)

    image_path = f'riddle_images/{riddle_id}.png'

    return jsonify({
        'success': True,
        'resolution': riddle['resolution'],
        'image': image_path
    })

@app.route('/solved')
def solved():
    return render_template('solved.html', teams=teams)

@app.route('/get_solved_riddles')
def get_solved_riddles():
    return jsonify(load_solved_riddles())

if __name__ == '__main__':
    app.run(debug=True)
