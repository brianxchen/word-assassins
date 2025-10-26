from flask import Flask, request, jsonify, render_template, session
import random
import os

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# In-memory data storage
game_state = {
    'players': {},
    'words': ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape']
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Store username in session
    session['username'] = username

    if username not in game_state['players']:
        game_state['players'][username] = {'score': 0, 'target': None, 'word': None}
        assign_target(username)
        # When a new player joins, reassign targets for all existing players
        for player in game_state['players']:
            if player != username:
                assign_target(player)
    
    # Ensure we always return the required fields
    player_data = game_state['players'][username]
    return jsonify({
        'target': player_data.get('target') or 'Waiting for more players...',
        'word': player_data.get('word') or 'No word yet',
        'score': player_data.get('score', 0),
        'username': username
    })

@app.route('/session', methods=['GET'])
def get_session():
    """Check if user has an active session"""
    username = session.get('username')
    if username and username in game_state['players']:
        player_data = game_state['players'][username]
        return jsonify({
            'target': player_data.get('target') or 'Waiting for more players...',
            'word': player_data.get('word') or 'No word yet',
            'score': player_data.get('score', 0),
            'username': username
        })
    return jsonify({'error': 'No active session'}), 401

@app.route('/kill', methods=['POST'])
def kill():
    username = session.get('username')
    if not username or username not in game_state['players']:
        return jsonify({'error': 'Invalid user'}), 400

    player = game_state['players'][username]
    
    # Check if player has a valid target
    if not player.get('target'):
        return jsonify({'error': 'No target available'}), 400
    
    player['score'] += 1
    assign_target(username)

    # Return the updated player data with proper null handling
    return jsonify({
        'target': player.get('target') or 'Waiting for more players...',
        'word': player.get('word') or 'No word yet',
        'score': player.get('score', 0),
        'username': username
    })

@app.route('/target', methods=['GET'])
def target():
    username = session.get('username')
    if not username or username not in game_state['players']:
        return jsonify({'error': 'Invalid user'}), 400

    player_data = game_state['players'][username]
    return jsonify({
        'target': player_data.get('target') or 'Waiting for more players...',
        'word': player_data.get('word') or 'No word yet',
        'score': player_data.get('score', 0),
        'username': username
    })

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the leaderboard sorted by score"""
    leaderboard = []
    for username, player_data in game_state['players'].items():
        leaderboard.append({
            'username': username,
            'score': player_data.get('score', 0)
        })
    
    # Sort by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(leaderboard)

@app.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username and username in game_state['players']:
        del game_state['players'][username]
        # Reassign targets for remaining players
        for player in game_state['players']:
            assign_target(player)
    session.clear()
    return jsonify({'success': True})

def assign_target(username):
    other_players = [p for p in game_state['players'] if p != username]
    if not other_players:
        # Handle case where there are no other players - don't assign anything
        game_state['players'][username]['target'] = None
        game_state['players'][username]['word'] = None
        return

    target_player = random.choice(other_players)
    target_word = random.choice(game_state['words'])

    # Assign the target and word
    game_state['players'][username]['target'] = target_player
    game_state['players'][username]['word'] = target_word

if __name__ == '__main__':
    app.run(debug=True)