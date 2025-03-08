import sqlite3
import os
from collections import defaultdict

def get_publishable_episodes():
    conn = sqlite3.connect('db/tv_vocab.db')
    cursor = conn.cursor()

    # Get all publishable episodes with their words that have levels
    cursor.execute('''
        SELECT e.season, e.episode, e.episode_name, e.episode_id,
               u.word, u.definition, u.level
        FROM episodes e
        LEFT JOIN uses u ON e.episode_id = u.episode_id
        WHERE u.level IS NOT NULL
          AND u.level != 'not vocabulary'
          AND e.publishable = 1
        ORDER BY e.season, e.episode, u.appearance_order
    ''')

    results = cursor.fetchall()
    conn.close()
    return results

def get_unique_seasons(episodes):
    return sorted(set(episode[0] for episode in episodes))

def get_unique_levels(episodes):
    levels = set(episode[6] for episode in episodes if episode[6] and episode[6] != 'not vocabulary')
    # Sort by educational progression
    level_order = {'elementary': 1, 'middle': 2, 'high': 3, 'college': 4, 'graduate': 5}
    return sorted(levels, key=lambda x: level_order[x])

def group_episodes_by_season(episodes):
    episodes_by_season = defaultdict(list)
    current_episode = None
    episode_words = {}  # Changed to dict to prevent duplicates, keyed by word

    for season, episode_num, name, episode_id, word, definition, level in episodes:
        # If we're starting a new episode
        if episode_id != current_episode:
            # If we had a previous episode, save it
            if current_episode is not None:
                episodes_by_season[current_season].append((current_episode_num, current_name, list(episode_words.values())))
            # Start new episode
            current_episode = episode_id
            current_season = season
            current_episode_num = episode_num
            current_name = name
            episode_words = {}

        # Add word and definition to current episode if they exist
        if word:
            # Keep only the latest definition for a word
            episode_words[word] = (word, definition if definition else '', level)

    # Don't forget to add the last episode
    if current_episode is not None:
        episodes_by_season[current_season].append((current_episode_num, current_name, list(episode_words.values())))

    return episodes_by_season

def generate_html(seasons, episodes_by_season, levels):
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    with open('reference.html', 'r') as f:
        template = f.read()

    # Generate level checkboxes HTML
    level_checkboxes = []
    for level in levels:
        level_checkboxes.append(f'''
            <label class="level-filter">
                <input type="checkbox" value="{level}" checked onchange="toggleLevel('{level}')">
                {level.title()}
            </label>''')
    level_checkboxes_html = '\n        '.join(level_checkboxes)

    # Generate season buttons HTML
    season_buttons = []
    for season in seasons:
        active = ' active' if season == seasons[0] else ''
        season_buttons.append(f'<button class="season-btn{active}">{season}</button>')
    season_buttons_html = '\n        '.join(season_buttons)

    # Generate episode cards HTML
    episode_cards = []
    for season in seasons:
        for episode_num, name, words in episodes_by_season[season]:
            # Generate vocabulary items HTML
            vocab_items = []
            for word, definition, level in words:
                definition_html = f'<div class="definition">{definition}</div>' if definition else ''
                vocab_items.append(f'''
                <div class="vocabulary-item level-{level}">
                    <div class="word"><a href="https://en.wiktionary.org/wiki/{word}" class="word-link">{word}</a></div>
                    {definition_html}
                </div>''')
            vocab_html = ''.join(vocab_items)

            # Generate episode card
            hidden = ' hidden' if season != seasons[0] else ''
            episode_cards.append(f'''
        <div class="episode-card season-{season}{hidden}">
            <h2 class="episode-title">Episode {episode_num}: {name}</h2>{vocab_html}
        </div>''')
    episode_cards_html = ''.join(episode_cards)

    # Add level filtering JavaScript
    level_filtering_js = '''
    <script>
    function toggleLevel(level) {
        const words = document.querySelectorAll(`.level-${level}`);
        const isChecked = document.querySelector(`input[value="${level}"]`).checked;
        words.forEach(word => {
            word.style.display = isChecked ? 'block' : 'none';
        });
    }
    </script>
    '''

    # Add level filtering styles
    level_filtering_css = '''
    <style>
    .level-filters {
        margin: 20px 0;
        text-align: center;
    }

    .level-filter {
        margin: 0 10px;
        cursor: pointer;
    }

    .level-filter input {
        margin-right: 5px;
    }

    .vocabulary-item {
        display: block;
    }
    
    .word-link {
        color: inherit;
        text-decoration: none;
        border-bottom: 1px dotted #999;
    }
    
    .word-link:hover {
        color: #ff6b6b;
        border-bottom: 1px solid #ff6b6b;
    }
    </style>
    '''

    # Find the insertion points in the template
    nav_start = template.find('<nav class="season-nav">')
    nav_end = template.find('</nav>', nav_start)
    main_start = template.find('<main class="episode-container">')
    main_end = template.find('</main>', main_start)
    head_end = template.find('</head>')

    # Construct the final HTML
    final_html = (
        template[:head_end] +
        level_filtering_css +
        level_filtering_js +
        template[head_end:nav_start] +
        '<div class="level-filters">\n        ' +
        '<span class="level-label">Show levels: </span>\n        ' +
        level_checkboxes_html +
        '\n    </div>\n    ' +
        template[nav_start:nav_start + len('<nav class="season-nav">\n        <span class="season-label">Season: </span>\n        ')] +
        season_buttons_html +
        template[nav_end:main_start + len('<main class="episode-container">')] +
        episode_cards_html +
        template[main_end:]
    )

    # Write the final HTML to a file
    with open('web/index.html', 'w') as f:
        f.write(final_html)

def main():
    episodes = get_publishable_episodes()
    seasons = get_unique_seasons(episodes)
    levels = get_unique_levels(episodes)
    episodes_by_season = group_episodes_by_season(episodes)
    generate_html(seasons, episodes_by_season, levels)

if __name__ == '__main__':
    main()
