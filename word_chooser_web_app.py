from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from utils.dictionary_utils import get_word_definitions

app = Flask(__name__)

def get_db():
    db = sqlite3.connect('db/tv_vocab.db')
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
        table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
        th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
        tr:hover { background-color: #f5f5f5; }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; }
        input[type="text"], input[type="number"] { padding: 0.5rem; width: 100%; box-sizing: border-box; }
        input[type="checkbox"] { margin-right: 0.5rem; }
        input[type="submit"] { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
        .word-list { margin-top: 2rem; }
        .word-item { margin: 0.5rem 0; }
        .word-header { display: flex; align-items: center; }
        .original-form { color: #666; margin-left: 0.5rem; }
        .definitions { margin-left: 2rem; margin-top: 0.5rem; display: none; }
        .definitions.show { display: block; }
        .definition-option { margin: 0.5rem 0; display: flex; align-items: flex-start; }
        .definition-option input[type="radio"] { margin-top: 0.25rem; margin-right: 0.5rem; }
        .definition-option label { margin: 0; }
        .season-header {
            background: #f8f9fa;
            padding: 0.75rem;
            margin: 1rem 0 0.5rem;
            border-radius: 4px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .season-header:hover {
            background: #e9ecef;
        }
        .season-content {
            display: none;
        }
        .season-content.show {
            display: block;
        }
        .toggle-icon {
            font-size: 1.2rem;
            transition: transform 0.2s;
        }
        .season-header.active .toggle-icon {
            transform: rotate(180deg);
        }
        .edit-link { 
            color: #007bff; 
            text-decoration: none; 
            font-size: 0.8em; 
            margin-left: 0.5rem; 
            cursor: pointer; 
        }
        .edit-link:hover { 
            text-decoration: underline; 
        }
        .word-edit-box {
            padding: 0.25rem;
            margin: -0.25rem 0;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: inherit;
            width: auto;
            display: none;
        }
    </style>
    <script>
        // Store selected definitions
        const selectedDefinitions = {};
        // Store original words for edit cancellation
        const originalWords = {};

        function toggleSeason(element) {
            element.classList.toggle('active');
            const content = element.nextElementSibling;
            content.classList.toggle('show');
        }
        
        function toggleDefinitions(word) {
            console.log('Toggling definitions for:', word);
            const checkbox = document.querySelector(`input[name="word_use_${word}"]`);
            const definitions = document.getElementById(`definitions_${word}`);
            console.log('Checkbox checked:', checkbox.checked);
            console.log('Definitions element:', definitions);
            if (checkbox.checked) {
                definitions.classList.add('show');
                // If we have a saved selection, reapply it
                if (selectedDefinitions[word]) {
                    const radio = definitions.querySelector(`input[type="radio"][value="${selectedDefinitions[word]}"]`);
                    if (radio) {
                        radio.checked = true;
                    }
                }
            } else {
                definitions.classList.remove('show');
            }
        }

        function saveDefinitionSelection(word, definition) {
            console.log('Saving definition for:', word, definition);
            selectedDefinitions[word] = definition;
        }

        function editWord(word) {
            const wordSpan = document.getElementById(`word_text_${word}`);
            const editBox = document.getElementById(`word_edit_${word}`);
            const editLink = document.getElementById(`word_edit_link_${word}`);
            
            // Store original word if not already stored
            if (!originalWords[word]) {
                originalWords[word] = wordSpan.textContent;
            }
            
            wordSpan.style.display = 'none';
            editBox.style.display = 'inline';
            editBox.value = wordSpan.textContent;
            editBox.focus();
            editLink.textContent = 'save';
            editLink.onclick = () => saveWord(word);
            
            // Add escape key handler
            editBox.onkeydown = (e) => {
                if (e.key === 'Escape') {
                    cancelEdit(word);
                } else if (e.key === 'Enter') {
                    saveWord(word);
                }
            };
        }

        function saveWord(word) {
            const wordSpan = document.getElementById(`word_text_${word}`);
            const editBox = document.getElementById(`word_edit_${word}`);
            const editLink = document.getElementById(`word_edit_link_${word}`);
            const newWord = editBox.value.trim();
            
            if (newWord && newWord !== word) {
                // Update the word text
                wordSpan.textContent = newWord;
                
                // Update the hidden input for form submission
                const hiddenInput = document.getElementById(`word_new_${word}`);
                hiddenInput.value = newWord;
                
                // Update any existing definition selection
                if (selectedDefinitions[word]) {
                    selectedDefinitions[newWord] = selectedDefinitions[word];
                    delete selectedDefinitions[word];
                }
            }
            
            wordSpan.style.display = 'inline';
            editBox.style.display = 'none';
            editLink.textContent = 'edit';
            editLink.onclick = () => editWord(word);
        }

        function cancelEdit(word) {
            const wordSpan = document.getElementById(`word_text_${word}`);
            const editBox = document.getElementById(`word_edit_${word}`);
            const editLink = document.getElementById(`word_edit_link_${word}`);
            
            // Restore original word
            if (originalWords[word]) {
                wordSpan.textContent = originalWords[word];
                delete originalWords[word];
            }
            
            wordSpan.style.display = 'inline';
            editBox.style.display = 'none';
            editLink.textContent = 'edit';
            editLink.onclick = () => editWord(word);
        }

        // Show definitions for pre-checked words on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM Content Loaded');
            const checkedWords = document.querySelectorAll('input[type="checkbox"][name^="word_use_"]:checked');
            console.log('Found checked words:', checkedWords.length);
            
            // Initialize selected definitions from any pre-selected radio buttons
            document.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
                const word = radio.name.replace('word_definition_', '');
                selectedDefinitions[word] = radio.value;
            });
            
            checkedWords.forEach(checkbox => {
                const word = checkbox.name.replace('word_use_', '');
                console.log('Showing definitions for:', word);
                toggleDefinitions(word);
            });
        });
    </script>
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
                        <div class="word-header">
                            <input type="checkbox" 
                                   id="word_use_{{ word.word }}"
                                   name="word_use_{{ word.word }}" 
                                   value="1" 
                                   {% if word.use %}checked{% endif %} 
                                   onchange="toggleDefinitions('{{ word.word }}')"
                                   onclick="toggleDefinitions('{{ word.word }}')">
                            <span id="word_text_{{ word.word }}">{{ word.word }}</span>
                            <input type="text" 
                                   id="word_edit_{{ word.word }}"
                                   class="word-edit-box"
                                   value="{{ word.word }}">
                            <input type="hidden"
                                   id="word_new_{{ word.word }}"
                                   name="word_new_{{ word.word }}"
                                   value="{{ word.word }}">
                            <a class="edit-link" 
                               id="word_edit_link_{{ word.word }}"
                               onclick="editWord('{{ word.word }}')">edit</a>
                            {% if word.original_word != word.word %}
                                <span class="original-form">({{ word.original_word }})</span>
                            {% endif %}
                        </div>
                        <div id="definitions_{{ word.word }}" class="definitions {% if word.use %}show{% endif %}">
                            {% for definition in get_word_definitions(word.word) %}
                            <div class="definition-option">
                                <input type="radio" 
                                       id="def_{{ word.word }}_{{ loop.index }}"
                                       name="word_definition_{{ word.word }}" 
                                       value="{{ definition }}" 
                                       {% if word.definition == definition %}checked{% endif %}
                                       onchange="saveDefinitionSelection('{{ word.word }}', this.value)">
                                <label for="def_{{ word.word }}_{{ loop.index }}">{{ definition }}</label>
                            </div>
                            {% endfor %}
                        </div>
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
        {% for season in sorted_seasons %}
            <div class="season-section">
                <div class="season-header" onclick="toggleSeason(this)">
                    <span>{% if season == 'Unknown Season' %}{{ season }}{% else %}Season {{ season }}{% endif %}</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="season-content">
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
                            {% for ep in episodes_by_season[season] %}
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
                </div>
            </div>
        {% endfor %}
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
    
    # Group episodes by season
    episodes_by_season = {}
    for ep in episodes:
        season = ep['season'] if ep['season'] is not None else 'Unknown Season'
        if season not in episodes_by_season:
            episodes_by_season[season] = []
        episodes_by_season[season].append(ep)
    
    # Sort seasons, putting "Unknown Season" at the end
    sorted_seasons = sorted(episodes_by_season.keys(), key=lambda x: float('inf') if x == 'Unknown Season' else x)
    
    db.close()
    return render_template_string(TEMPLATE, episodes_by_season=episodes_by_season, sorted_seasons=sorted_seasons)

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
        
        # Update word usage and definitions
        for key, value in request.form.items():
            if key.startswith('word_use_'):
                word = key.replace('word_use_', '')
                use_word = value == '1'
                
                # Check if word has been edited
                new_word = request.form.get(f'word_new_{word}')
                if new_word and new_word != word:
                    # Update the word in both tables
                    db.execute('UPDATE words SET word = ? WHERE word = ?', 
                             (new_word, word))
                    db.execute('UPDATE uses SET word = ? WHERE word = ?', 
                             (new_word, word))
                    # Use the new word for the rest of the updates
                    word = new_word
                
                db.execute('UPDATE words SET use = ? WHERE word = ?', 
                          (use_word, word))
                
                # If the word is being used, update its definition
                if use_word:
                    definition = request.form.get(f'word_definition_{word}')
                    if definition:
                        db.execute('''
                            UPDATE uses 
                            SET definition = ?
                            WHERE word = ? AND episode_id = ?
                        ''', (definition, word, episode_id))
        
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
                MIN(u.original_word) as original_word,
                MIN(u.definition) as definition
            FROM words w
            JOIN uses u ON w.word = u.word
            WHERE u.episode_id = ? AND w.is_vocabulary = 1
            GROUP BY w.word
        )
        SELECT word, use, original_word, definition
        FROM FirstAppearance
        ORDER BY first_appearance_id
    ''', (episode_id,)).fetchall()
    
    db.close()
    return render_template_string(TEMPLATE, episode=episode, words=words, get_word_definitions=get_word_definitions)

if __name__ == '__main__':
    app.run(debug=True)
