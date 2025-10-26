from flask import Flask, request, jsonify, render_template

app = Flask(__name__, static_folder='static', template_folder='static')

# In-memory data storage
game_state = {
    'players': {},
    'words': ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape']
}

@app.route('/')
def index():
    return render_template('index.html')

import random

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    if username not in game_state['players']:
        game_state['players'][username] = {'score': 0, 'target': None, 'word': None}
        assign_target(username)
    
    # Ensure we always return the required fields, even if no target is assigned
    player_data = game_state['players'][username]
    return jsonify({
        'target': player_data.get('target', 'No targets available'),
        'word': player_data.get('word', 'No word assigned'),
        'score': player_data.get('score', 0)
    })

@app.route('/kill', methods=['POST'])
def kill():
    username = request.json.get('username')
    if not username or username not in game_state['players']:
        return jsonify({'error': 'Invalid user'}), 400

    player = game_state['players'][username]
    player['score'] += 1
    assign_target(username)

    return jsonify(player)

@app.route('/target', methods=['GET'])
def target():
    username = request.args.get('username')
    if not username or username not in game_state['players']:
        return jsonify({'error': 'Invalid user'}), 400

    return jsonify(game_state['players'][username])

def assign_target(username):
    other_players = [p for p in game_state['players'] if p != username]
    if not other_players:
        # Handle case where there are no other players
        game_state['players'][username]['target'] = 'No targets available'
        game_state['players'][username]['word'] = 'Waiting for other players'
        return

    target_player = random.choice(other_players)
    target_word = random.choice(game_state['words'])

    # This was missing - actually assign the target and word
    game_state['players'][username]['target'] = target_player
    game_state['players'][username]['word'] = target_word

if __name__ == '__main__':
    app.run(debug=True)