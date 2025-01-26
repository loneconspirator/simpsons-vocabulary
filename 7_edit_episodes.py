from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db():
    db = sqlite3.connect('tv_vocab.db')
    db.row_factory = sqlite3.Row
    return db

# HTML template for both index and edit pages
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{% if episode %}Edit Episode {{ episode.episode_id }}{% else %}Episodes{% endif %}</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
        tr:hover { background-color: #f5f5f5; }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; }
        input[type="text"], input[type="number"] { padding: 0.5rem; width: 100%; box-sizing: border-box; }
        input[type="checkbox"] { margin-right: 0.5rem; }
        input[type="submit"] { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
        .word-list { margin-top: 2rem; }
        .word-item { display: flex; align-items: center; margin: 0.5rem 0; }
        .original-form { color: #666; margin-left: 0.5rem; }
    </style>
</head>
<body>
    {% if episode %}
        <h1>Edit Episode {{ episode.episode_id }}</h1>
        <form method="POST">
            <div class="form-group">
                <label>Episode ID: {{ episode.episode_id }}</label>
            </div>
            <div class="form-group">
                <label>Episode Name:</label>
                <input type="text" name="episode_name" value="{{ episode.episode_name or '' }}">
            </div>
            <div class="form-group">
                <label>Season:</label>
                <input type="number" name="season" value="{{ episode.season or '' }}">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="publishable" value="1" {% if episode.publishable %}checked{% endif %}>
                    Publishable
                </label>
            </div>
            
            <div class="word-list">
                <h2>Vocabulary Words</h2>
                {% for word in words %}
                    <div class="word-item">
                        <label>
                            <input type="checkbox" name="word_use_{{ word.word }}" value="1" {% if word.use %}checked{% endif %}>
                            {{ word.word }}
                            {% if word.original_word != word.word %}
                                <span class="original-form">({{ word.original_word }})</span>
                            {% endif %}
                        </label>
                    </div>
                {% endfor %}
            </div>
            
            <div class="form-group">
                <input type="submit" value="Save Changes">
            </div>
        </form>
        <p><a href="{{ url_for('index') }}">Back to Episodes List</a></p>
    {% else %}
        <h1>Episodes</h1>
        <table>
            <thead>
                <tr>
                    <th>Episode ID</th>
                    <th>Name</th>
                    <th>Season</th>
                    <th>Publishable</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for ep in episodes %}
                    <tr>
                        <td>{{ ep.episode_id }}</td>
                        <td>{{ ep.episode_name or '' }}</td>
                        <td>{{ ep.season or '' }}</td>
                        <td>{{ '✓' if ep.publishable else '' }}</td>
                        <td><a href="{{ url_for('edit', episode_id=ep.episode_id) }}">Edit</a></td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    db = get_db()
    episodes = db.execute('''
        SELECT episode_id, episode_name, publishable, season 
        FROM episodes 
        ORDER BY 
            CASE 
                WHEN season IS NULL THEN 1 
                ELSE 0 
            END,
            season,
            episode_id
    ''').fetchall()
    db.close()
    return render_template_string(TEMPLATE, episodes=episodes)

@app.route('/edit/<episode_id>', methods=['GET', 'POST'])
def edit(episode_id):
    db = get_db()
    
    if request.method == 'POST':
        # Update episode
        db.execute('''
            UPDATE episodes 
            SET episode_name = ?, publishable = ?, season = ?
            WHERE episode_id = ?
        ''', (
            request.form.get('episode_name'),
            request.form.get('publishable') == '1',
            request.form.get('season') or None,
            episode_id
        ))
        
        # Update word usage
        for key, value in request.form.items():
            if key.startswith('word_use_'):
                word = key.replace('word_use_', '')
                db.execute('UPDATE words SET use = ? WHERE word = ?', 
                          (value == '1', word))
        
        db.commit()
        return redirect(url_for('index'))
    
    # Get episode data
    episode = db.execute('SELECT * FROM episodes WHERE episode_id = ?', 
                        (episode_id,)).fetchone()
    
    # Get vocabulary words for this episode in order of appearance
    words = db.execute('''
        WITH FirstAppearance AS (
            SELECT 
                w.word,
                w.use,
                MIN(u.id) as first_appearance_id,
                MIN(u.original_word) as original_word
            FROM words w
            JOIN uses u ON w.word = u.word
            WHERE u.episode_id = ? AND w.is_vocabulary = 1
            GROUP BY w.word
        )
        SELECT word, use, original_word
        FROM FirstAppearance
        ORDER BY first_appearance_id
    ''', (episode_id,)).fetchall()
    
    db.close()
    return render_template_string(TEMPLATE, episode=episode, words=words)

if __name__ == '__main__':
    app.run(debug=True)
