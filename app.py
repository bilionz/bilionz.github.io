from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

app = Flask(__name__)

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
    return render_template('index.html')

@app.route('/register_infected')
def register_infected():
    return render_template('register_infected.html')

@app.route('/add_infected', methods=['POST'])
def add_infected():
    data = request.json
    team_name = data.get('teamName')
    player_name = data.get('playerName')

    if not team_name or not player_name:
        return jsonify({'success': False, 'error': 'Both fields are required.'})

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
    data = request.json
    team_name = data.get('teamName')
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
        
        return jsonify({
            'success': True,
            'resolution': riddle['resolution'],
            'image': image_path
        })
        # return jsonify({'success': False, 'error': 'Riddle part already solved.'})

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
