from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from utils.dictionary_utils import get_word_definitions

app = Flask(__name__, static_url_path='/static')

def get_db():
    db = sqlite3.connect('db/tv_vocab.db')
    db.row_factory = sqlite3.Row
    return db

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/episodes')
def get_episodes():
    db = get_db()
    episodes = db.execute('''
        SELECT episode_id, episode_name, season, episode_id as episode_number, publishable
        FROM episodes
        ORDER BY
            CASE WHEN season IS NULL THEN 1 ELSE 0 END,
            season,
            episode_id
    ''').fetchall()
    return jsonify([dict(episode) for episode in episodes])

@app.route('/api/episodes/<string:episode_id>')
def get_episode(episode_id):
    db = get_db()
    episode = db.execute('''
        SELECT episode_id, episode_name, season, episode_id as episode_number, publishable
        FROM episodes
        WHERE episode_id = ?
    ''', [episode_id]).fetchone()

    if not episode:
        return jsonify({'error': 'Episode not found'}), 404

    words = db.execute('''
        SELECT DISTINCT w.word, u.original_word as original_form,
               u.use as is_used, u.definition as selected_definition,
               u.level
        FROM words w
        INNER JOIN uses u ON w.word = u.word
        WHERE w.is_vocabulary = 1 AND u.episode_id = ?
        ORDER BY u.appearance_order
    ''', [episode_id]).fetchall()

    episode_data = dict(episode)
    episode_data['words'] = [dict(word) for word in words]
    
    return jsonify(episode_data)

@app.route('/api/episodes/<string:episode_id>/all-words')
def get_all_episode_words(episode_id):
    db = get_db()
    words = db.execute('''
        SELECT DISTINCT w.word, u.original_word as original_form,
               u.use as is_used, w.is_vocabulary,
               MIN(u.appearance_order) as first_appearance
        FROM words w
        INNER JOIN uses u ON w.word = u.word
        WHERE u.episode_id = ?
        GROUP BY w.word, u.original_word, u.use, w.is_vocabulary
        ORDER BY first_appearance
    ''', [episode_id]).fetchall()
    
    return jsonify([dict(word) for word in words])

@app.route('/api/episodes/<string:episode_id>/words/<string:word>', methods=['PUT'])
def update_word(episode_id, word):
    db = get_db()
    data = request.json
    new_word = data.get('new_word')

    if new_word:
        # First check if the new word exists in the words table
        existing_word = db.execute('SELECT word FROM words WHERE word = ?', [new_word]).fetchone()
        if not existing_word:
            # Add new word to words table with is_vocabulary=1
            db.execute('INSERT INTO words (word, is_vocabulary) VALUES (?, 1)', [new_word])

        # Update the word in uses table
        db.execute('''
            UPDATE uses
            SET word = ?
            WHERE word = ? AND episode_id = ?
        ''', [new_word, word, episode_id])

        # Check if the old word is still used anywhere
        still_used = db.execute('SELECT 1 FROM uses WHERE word = ? LIMIT 1', [word]).fetchone()
        if not still_used:
            # If old word is not used anywhere else, remove it from words table
            db.execute('DELETE FROM words WHERE word = ?', [word])

        db.commit()
        return jsonify({'status': 'success'})

    return jsonify({'error': 'New word not provided'}), 400

@app.route('/api/episodes/<string:episode_id>/words/<string:word>/use', methods=['PUT'])
def update_word_use(episode_id, word):
    db = get_db()
    data = request.json
    is_used = data.get('is_used')

    if is_used is not None:
        db.execute('''
            UPDATE uses
            SET use = ?
            WHERE word = ? AND episode_id = ?
        ''', [1 if is_used else 0, word, episode_id])


        db.commit()
        return jsonify({'status': 'success'})

    return jsonify({'error': 'is_used not provided'}), 400

@app.route('/api/episodes/<string:episode_id>/words/<string:word>/definition', methods=['PUT'])
def update_word_definition(episode_id, word):
    db = get_db()
    data = request.json
    definition = data.get('definition')

    if definition:
        db.execute('''
            UPDATE uses
            SET definition = ?
            WHERE word = ? AND episode_id = ?
        ''', [definition, word, episode_id])
        db.commit()
        return jsonify({'status': 'success'})

    return jsonify({'error': 'Definition not provided'}), 400

@app.route('/api/episodes/<string:episode_id>/words/<string:word>/level', methods=['PUT'])
def update_word_level(episode_id, word):
    db = get_db()
    data = request.json
    level = data.get('level')
    
    # Convert empty string to NULL
    if level == '':
        level = None
        
    # Update the level in uses table
    db.execute('''
        UPDATE uses
        SET level = ?
        WHERE word = ? AND episode_id = ?
    ''', [level, word, episode_id])
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/words/<string:word>/vocabulary', methods=['PUT'])
def update_word_vocabulary(word):
    db = get_db()
    data = request.json
    is_vocabulary = data.get('is_vocabulary')
    
    if is_vocabulary is not None:
        db.execute('''
            UPDATE words
            SET is_vocabulary = ?
            WHERE word = ?
        ''', [1 if is_vocabulary else 0, word])
        db.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'is_vocabulary not provided'}), 400

@app.route('/api/episodes/<string:episode_id>/publishable', methods=['PUT'])
def update_episode_publishable(episode_id):
    db = get_db()
    data = request.json
    publishable = data.get('publishable')
    
    if publishable is not None:
        db.execute('''
            UPDATE episodes
            SET publishable = ?
            WHERE episode_id = ?
        ''', [1 if publishable else 0, episode_id])
        db.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'publishable not provided'}), 400

@app.route('/api/episodes/<string:episode_id>/uses', methods=['POST'])
def create_word_use(episode_id):
    """Create a new word use for an episode. If the word doesn't exist, create it."""
    data = request.get_json()
    word = data.get('word', '').strip().lower()
    
    if not word:
        return jsonify({'error': 'Word is required'}), 400
        
    db = get_db()
    try:
        # First, ensure the word exists in the words table
        db.execute('''
            INSERT OR IGNORE INTO words (word, is_vocabulary)
            VALUES (?, 0)
        ''', [word])
        
        # Get the max appearance_order for this episode
        max_order = db.execute('''
            SELECT COALESCE(MAX(appearance_order), 0)
            FROM uses
            WHERE episode_id = ?
        ''', [episode_id]).fetchone()[0]
        
        # Create the use
        db.execute('''
            INSERT INTO uses (word, episode_id, use, appearance_order)
            VALUES (?, ?, 0, ?)
        ''', [word, episode_id, max_order + 1])
        
        db.commit()
        
        # Return the new word with its definitions
        word_data = {
            'word': word,
            'is_used': False,
            'definitions': get_word_definitions(word)
        }
        return jsonify(word_data)
        
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/episodes/<string:episode_id>/reorder', methods=['POST'])
def reorder_words(episode_id):
    """Update the appearance_order of words in an episode."""
    data = request.get_json()
    word_orders = data.get('wordOrders', [])
    
    if not word_orders:
        return jsonify({'error': 'No word orders provided'}), 400
        
    db = get_db()
    try:
        # Update each word's appearance_order
        for order in word_orders:
            word = order.get('word')
            new_order = order.get('order')
            if word is not None and new_order is not None:
                db.execute('''
                    UPDATE uses 
                    SET appearance_order = ? 
                    WHERE word = ? AND episode_id = ?
                ''', [new_order, word, episode_id])
        
        db.commit()
        return jsonify({'success': True})
        
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/words/<string:word>/definitions')
def get_word_definitions_api(word):
    """Separate endpoint to fetch definitions for a single word"""
    definitions = get_word_definitions(word)
    return jsonify(definitions)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
