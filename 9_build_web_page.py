import sqlite3
import os
from collections import defaultdict

def get_publishable_episodes():
    conn = sqlite3.connect('db/tv_vocab.db')
    cursor = conn.cursor()

    # Get all publishable episodes with their words
    cursor.execute('''
        SELECT e.season, e.episode, e.episode_name, e.episode_id, u.word, u.definition
        FROM episodes e
        LEFT JOIN uses u ON e.episode_id = u.episode_id
        WHERE e.publishable = TRUE
          AND u.use = TRUE
        ORDER BY e.season, e.episode, u.appearance_order
    ''')

    results = cursor.fetchall()
    conn.close()
    return results

def get_unique_seasons(episodes):
    return sorted(set(episode[0] for episode in episodes))

def group_episodes_by_season(episodes):
    episodes_by_season = defaultdict(list)
    current_episode = None
    episode_words = {}  # Changed to dict to prevent duplicates, keyed by word

    for season, episode_num, name, episode_id, word, definition in episodes:
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
            episode_words[word] = (word, definition if definition else '')

    # Don't forget to add the last episode
    if current_episode is not None:
        episodes_by_season[current_season].append((current_episode_num, current_name, list(episode_words.values())))

    return episodes_by_season

def generate_html(seasons, episodes_by_season):
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    with open('reference.html', 'r') as f:
        template = f.read()

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
            for word, definition in words:
                definition_html = f'<div class="definition">{definition}</div>' if definition else ''
                vocab_items.append(f'''
                <div class="vocabulary-item">
                    <div class="word">{word}</div>
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

    # Find the insertion points in the template
    nav_start = template.find('<nav class="season-nav">')
    nav_end = template.find('</nav>', nav_start)
    main_start = template.find('<main class="episode-container">')
    main_end = template.find('</main>', main_start)

    # Construct the final HTML
    final_html = (
        template[:nav_start + len('<nav class="season-nav">\n        <span class="season-label">Season: </span>\n        ')] +
        season_buttons_html +
        template[nav_end - 1:main_start + len('<main class="episode-container">')] +
        episode_cards_html +
        template[main_end - 1:]
    )

    # Create web directory if it doesn't exist
    os.makedirs('web', exist_ok=True)

    # Write the output file
    with open('web/index.html', 'w') as f:
        f.write(final_html)

def main():
    # Get all publishable episodes and their words
    episodes = get_publishable_episodes()

    # Get unique seasons
    seasons = get_unique_seasons(episodes)

    # Group episodes by season
    episodes_by_season = group_episodes_by_season(episodes)

    # Generate the HTML file
    generate_html(seasons, episodes_by_season)

if __name__ == '__main__':
    main()
