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
        level_initial = level[0].upper()
        level_checkboxes.append(f'''
            <label class="level-filter">
                <input type="checkbox" value="{level}" checked onchange="toggleLevel('{level}')">
                <span class="level-icon level-{level}">{level_initial}</span>
                <span class="level-label-text">{level.title()}</span>
            </label>''')
    level_checkboxes_html = '\n        '.join(level_checkboxes)

    # Generate season buttons HTML
    season_buttons = []
    for season in seasons:
        active = ' active' if season == seasons[0] else ''
        season_buttons.append(f'<button class="season-btn{active}">{season}</button>')
    season_buttons_html = '\n        '.join(season_buttons)
    
    # Generate episode links container for each season
    episode_links_containers = []
    for season in seasons:
        episode_links = []
        for episode_num, _, _ in episodes_by_season[season]:
            episode_links.append(f'<a href="#episode-{season}-{episode_num}" class="episode-link">{episode_num}</a>')
        
        hidden = ' hidden' if season != seasons[0] else ''
        episode_links_html = '\n            '.join(episode_links)
        episode_links_containers.append(f'''
        <div class="episode-links-container season-{season}-episodes{hidden}">
            {episode_links_html}
        </div>''')
    
    episode_links_containers_html = ''.join(episode_links_containers)

    # Generate episode cards HTML
    episode_cards = []
    for season in seasons:
        for episode_num, name, words in episodes_by_season[season]:
            # Generate vocabulary items HTML
            vocab_items = []
            for word, definition, level in words:
                level_initial = level[0].upper()
                definition_html = f'<div class="definition">{definition}</div>' if definition else ''
                vocab_items.append(f'''
                <div class="vocabulary-item" data-level="{level}">
                    <div class="word">
                        <a href="https://en.wiktionary.org/wiki/{word}" class="word-link">{word}</a>
                        <span class="level-icon level-{level}">{level_initial}</span>
                    </div>
                    {definition_html}
                </div>''')
            vocab_html = ''.join(vocab_items)

            # Generate episode card
            hidden = ' hidden' if season != seasons[0] else ''
            episode_cards.append(f'''
        <div id="episode-{season}-{episode_num}" class="episode-card season-{season}{hidden}">
            <h2 class="episode-title">Episode {episode_num}: {name}</h2>{vocab_html}
        </div>''')
    episode_cards_html = ''.join(episode_cards)

    # Add episode navigation JavaScript
    episode_nav_js = '''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const seasonButtons = document.querySelectorAll('.season-btn');

        seasonButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                seasonButtons.forEach(btn => btn.classList.remove('active'));

                // Add active class to clicked button
                this.classList.add('active');

                // Get the season number
                const season = this.textContent;

                // Hide all episode cards with transition
                const allEpisodeCards = document.querySelectorAll('.episode-card');
                allEpisodeCards.forEach(card => {
                    if (card.classList.contains(`season-${season}`)) {
                        card.classList.remove('hidden');
                        // Small delay to ensure transform happens
                        setTimeout(() => {
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, 50);
                    } else {
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(10px)';
                        // Add hidden class after transition
                        setTimeout(() => {
                            card.classList.add('hidden');
                        }, 300);
                    }
                });
                
                // Show episode links for the selected season
                const allEpisodeLinks = document.querySelectorAll('.episode-links-container');
                allEpisodeLinks.forEach(container => {
                    if (container.classList.contains(`season-${season}-episodes`)) {
                        container.classList.remove('hidden');
                    } else {
                        container.classList.add('hidden');
                    }
                });
            });
        });
        
        // Add smooth scrolling for episode links
        document.querySelectorAll('.episode-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 100, // Offset to account for fixed header
                        behavior: 'smooth'
                    });
                }
            });
        });
    });
    </script>
    '''

    # Add level filtering JavaScript
    level_filtering_js = '''
    <script>
    function toggleLevel(level) {
        const words = document.querySelectorAll(`[data-level="${level}"]`);
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
        margin: 0 12px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
    }

    .level-filter input {
        margin-right: 6px;
    }

    .level-label-text {
        margin-left: 6px;
    }
    
    .season-nav, .episode-nav {
        padding: 20px;
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .season-label, .episode-label {
        color: #ff6b6b;
        font-size: 1.2em;
        margin-right: 10px;
    }
    
    /* Clear the existing season-nav styles from the template */
    .navigation-container {
        display: flex;
        flex-direction: column;
    }

    .vocabulary-item {
        display: block;
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eee;
    }

    .vocabulary-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
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

    .word {
        display: flex;
        align-items: center;
        font-weight: bold;
    }

    .level-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        font-size: 10px;
        font-weight: bold;
        margin-left: 8px;
        color: white;
    }

    .level-elementary {
        background-color: #FED90F; /* Simpsons Yellow */
    }

    .level-middle {
        background-color: #3D99F6; /* Marge's Hair Blue */
    }

    .level-high {
        background-color: #FB503B; /* Lisa's Dress Red */
    }

    .level-college {
        background-color: #82D440; /* Marge's Dress Green */
    }

    .level-graduate {
        background-color: #A67EB7; /* Purple (Patty/Selma hair) */
    }
    
    .episode-links-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        transition: opacity 0.3s ease;
    }
    
    .episode-links-container.hidden {
        display: none;
    }
    
    .episode-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: white;
        color: #ff6b6b;
        text-decoration: none;
        border: 1px solid #ff6b6b;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .episode-link:hover {
        background-color: #ff6b6b;
        color: white;
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
        episode_nav_js +
        template[head_end:nav_start] +
        '<div class="level-filters">\n        ' +
        '<span class="level-label">Show levels: </span>\n        ' +
        level_checkboxes_html +
        '\n    </div>\n    ' +
        '<div class="navigation-container">\n' +
        '    <nav class="season-nav">\n        <span class="season-label">Season: </span>\n        ' +
        season_buttons_html +
        '\n    </nav>\n' +
        '    <nav class="episode-nav">\n        <span class="episode-label">Episode: </span>' +
        episode_links_containers_html +
        '\n    </nav>\n' +
        '</div>' +
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
