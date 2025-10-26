from flask import Flask, request, jsonify, render_template, session
import random
import os
from datetime import datetime
import pytz

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Admin username from environment variable
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin-default')

WORDS_STRING = os.environ.get('WORDS', 'apple,banana,cherry,date,elderberry,fig,grape')
WORDS_LIST = [word.strip() for word in WORDS_STRING.split(',')]

# In-memory data storage
game_state = {
    'players': {},
    'words': WORDS_LIST,
    'kill_log': []  # New: store recent kills
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

    # Check if admin
    if username == ADMIN_USERNAME:
        session['is_admin'] = True
        return jsonify({
            'target': 'Admin Mode',
            'word': 'You are the admin',
            'score': 0,
            'username': username,
            'is_admin': True
        })

    if username not in game_state['players']:
        game_state['players'][username] = {'score': 0, 'target': None, 'word': None, 'active': True, 'passes_left': 5}
    else:
        # Player is returning, mark them as active again
        game_state['players'][username]['active'] = True
        # Ensure passes_left exists for returning players
        if 'passes_left' not in game_state['players'][username]:
            game_state['players'][username]['passes_left'] = 5
    
    assign_target(username)
    # When a player joins/rejoins, reassign targets for all active players
    for player in game_state['players']:
        if player != username and game_state['players'][player].get('active'):
            assign_target(player)
    
    # Ensure we always return the required fields
    player_data = game_state['players'][username]
    return jsonify({
        'target': player_data.get('target') or 'Waiting for more players...',
        'word': player_data.get('word') or 'No word yet',
        'score': player_data.get('score', 0),
        'passes_left': player_data.get('passes_left', 5),
        'username': username,
        'is_admin': False
    })

@app.route('/session', methods=['GET'])
def get_session():
    """Check if user has an active session"""
    username = session.get('username')
    
    # Handle admin session
    if username == ADMIN_USERNAME and session.get('is_admin'):
        return jsonify({
            'target': 'Admin Mode',
            'word': 'You are the admin',
            'score': 0,
            'username': username,
            'is_admin': True
        })
    
    if username and username in game_state['players'] and game_state['players'][username].get('active'):
        player_data = game_state['players'][username]
        # Ensure passes_left exists for existing players
        if 'passes_left' not in player_data:
            player_data['passes_left'] = 5
        return jsonify({
            'target': player_data.get('target') or 'Waiting for more players...',
            'word': player_data.get('word') or 'No word yet',
            'score': player_data.get('score', 0),
            'passes_left': player_data.get('passes_left', 5),
            'username': username,
            'is_admin': False
        })
    return jsonify({'error': 'No active session'}), 401

@app.route('/kill', methods=['POST'])
def kill():
    username = session.get('username')
    if not username or username not in game_state['players'] or username == ADMIN_USERNAME:
        return jsonify({'error': 'Invalid user or admin cannot kill'}), 400

    player = game_state['players'][username]
    
    # Check if player is active and has a valid target
    if not player.get('active') or not player.get('target') or not player.get('word'):
        return jsonify({'error': 'No target available'}), 400
    
    # Get current time in Pacific timezone (automatically handles PST/PDT)
    pacific = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific)
    
    # Determine if we're in PST or PDT
    timezone_name = "PST" if current_time.dst().total_seconds() == 0 else "PDT"
    
    # Log the kill
    kill_entry = {
        'killer': username,
        'target': player['target'],
        'word': player['word'],
        'timestamp': current_time.strftime(f'%Y-%m-%d %H:%M:%S {timezone_name}')
    }
    
    # Add to kill log (keep only last 20 kills)
    game_state['kill_log'].insert(0, kill_entry)
    if len(game_state['kill_log']) > 20:
        game_state['kill_log'] = game_state['kill_log'][:20]
    
    player['score'] += 1
    assign_target(username)

    # Return the updated player data with proper null handling
    return jsonify({
        'target': player.get('target') or 'Waiting for more players...',
        'word': player.get('word') or 'No word yet',
        'score': player.get('score', 0),
        'passes_left': player.get('passes_left', 5),
        'username': username
    })

@app.route('/pass', methods=['POST'])
def pass_target():
    """Allow player to skip their current target and word (limited uses)"""
    username = session.get('username')
    if not username or username not in game_state['players'] or username == ADMIN_USERNAME:
        return jsonify({'error': 'Invalid user or admin cannot pass'}), 400

    player = game_state['players'][username]
    
    # Check if player is active and has passes left
    if not player.get('active'):
        return jsonify({'error': 'Player not active'}), 400
    
    if player.get('passes_left', 0) <= 0:
        return jsonify({'error': 'No passes remaining'}), 400
    
    if not player.get('target') or not player.get('word'):
        return jsonify({'error': 'No target to pass'}), 400
    
    # Use a pass and get a completely new target and word
    player['passes_left'] -= 1
    assign_target(username)

    # Return the updated player data
    return jsonify({
        'target': player.get('target') or 'Waiting for more players...',
        'word': player.get('word') or 'No word yet',
        'score': player.get('score', 0),
        'passes_left': player.get('passes_left', 0),
        'username': username
    })

@app.route('/target', methods=['GET'])
def target():
    username = session.get('username')
    
    # Handle admin
    if username == ADMIN_USERNAME and session.get('is_admin'):
        return jsonify({
            'target': 'Admin Mode',
            'word': 'You are the admin',
            'score': 0,
            'username': username,
            'is_admin': True
        })
    
    if not username or username not in game_state['players'] or not game_state['players'][username].get('active'):
        return jsonify({'error': 'Invalid user'}), 400

    player_data = game_state['players'][username]
    # Ensure passes_left exists
    if 'passes_left' not in player_data:
        player_data['passes_left'] = 5
    
    return jsonify({
        'target': player_data.get('target') or 'Waiting for more players...',
        'word': player_data.get('word') or 'No word yet',
        'score': player_data.get('score', 0),
        'passes_left': player_data.get('passes_left', 5),
        'username': username,
        'is_admin': False
    })

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the leaderboard sorted by score"""
    leaderboard = []
    for username, player_data in game_state['players'].items():
        # Don't include admin in leaderboard, but include all players (active and inactive)
        if username != ADMIN_USERNAME:
            leaderboard.append({
                'username': username,
                'score': player_data.get('score', 0),
                'active': player_data.get('active', False),
                'passes_left': player_data.get('passes_left', 5)
            })
    
    # Sort by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(leaderboard)

@app.route('/kill-log', methods=['GET'])
def get_kill_log():
    """Get the recent kill log"""
    return jsonify(game_state['kill_log'])

# Admin routes
@app.route('/admin/reset', methods=['POST'])
def admin_reset_game():
    """Reset the entire game state"""
    if not session.get('is_admin') or session.get('username') != ADMIN_USERNAME:
        return jsonify({'error': 'Unauthorized'}), 403
    
    game_state['players'] = {}
    game_state['kill_log'] = []  # Also clear kill log
    return jsonify({'success': 'Game reset successfully'})

@app.route('/admin/remove-player', methods=['POST'])
def admin_remove_player():
    """Remove a specific player"""
    if not session.get('is_admin') or session.get('username') != ADMIN_USERNAME:
        return jsonify({'error': 'Unauthorized'}), 403
    
    player_to_remove = request.json.get('username')
    if not player_to_remove:
        return jsonify({'error': 'Username required'}), 400
    
    if player_to_remove in game_state['players']:
        del game_state['players'][player_to_remove]
        # Reassign targets for remaining active players
        for player in game_state['players']:
            if game_state['players'][player].get('active'):
                assign_target(player)
        return jsonify({'success': f'Player {player_to_remove} removed'})
    
    return jsonify({'error': 'Player not found'}), 404

@app.route('/admin/add-score', methods=['POST'])
def admin_add_score():
    """Add points to a player's score"""
    if not session.get('is_admin') or session.get('username') != ADMIN_USERNAME:
        return jsonify({'error': 'Unauthorized'}), 403
    
    username = request.json.get('username')
    points = request.json.get('points', 1)
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    if username in game_state['players']:
        game_state['players'][username]['score'] += points
        return jsonify({'success': f'Added {points} points to {username}'})
    
    return jsonify({'error': 'Player not found'}), 404

@app.route('/admin/reset-passes', methods=['POST'])
def admin_reset_passes():
    """Reset passes for a specific player"""
    if not session.get('is_admin') or session.get('username') != ADMIN_USERNAME:
        return jsonify({'error': 'Unauthorized'}), 403
    
    username = request.json.get('username')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    if username in game_state['players']:
        game_state['players'][username]['passes_left'] = 5
        return jsonify({'success': f'Reset passes for {username}'})
    
    return jsonify({'error': 'Player not found'}), 404

@app.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username and username in game_state['players'] and username != ADMIN_USERNAME:
        # Mark player as inactive but don't remove them from the game
        game_state['players'][username]['active'] = False
        game_state['players'][username]['target'] = None
        game_state['players'][username]['word'] = None
        
        # Reassign targets for remaining active players
        for player in game_state['players']:
            if game_state['players'][player].get('active'):
                assign_target(player)
    
    session.clear()
    return jsonify({'success': True})

def assign_target(username):
    # Only assign targets from active players (excluding admin)
    other_players = [p for p in game_state['players'] 
                    if p != username 
                    and p != ADMIN_USERNAME 
                    and game_state['players'][p].get('active')]
    
    if not other_players:
        # Handle case where there are no other active players
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