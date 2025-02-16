// Store selected definitions and original words
const selectedDefinitions = {};
const originalWords = {};
let currentEpisode = null;

// Fetch episodes grouped by season
async function fetchEpisodes() {
    const response = await fetch('/api/episodes');
    const episodes = await response.json();
    return groupEpisodesBySeason(episodes);
}

function groupEpisodesBySeason(episodes) {
    return episodes.reduce((acc, episode) => {
        const season = episode.season;
        if (!acc[season]) acc[season] = [];
        acc[season].push(episode);
        return acc;
    }, {});
}

// Render episodes list
async function renderEpisodesList() {
    const seasonsContainer = document.getElementById('seasons-container');
    const groupedEpisodes = await fetchEpisodes();
    
    seasonsContainer.innerHTML = Object.entries(groupedEpisodes)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([season, episodes]) => `
            <div class="season">
                <div class="season-header" onclick="toggleSeason(this)">
                    <span>Season ${season || 'Unknown'}</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="season-content">
                    <table>
                        <thead>
                            <tr>
                                <th>Episode</th>
                                <th>Name</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${episodes.sort((a, b) => a.episode_number - b.episode_number)
                                .map(episode => `
                                    <tr>
                                        <td>${episode.episode_number}</td>
                                        <td>${episode.episode_name}</td>
                                        <td>
                                            <a href="#" onclick="editEpisode('${episode.episode_id}'); return false;" 
                                               class="edit-link">Edit</a>
                                        </td>
                                    </tr>
                                `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `).join('');
}

// Toggle season collapse/expand
function toggleSeason(element) {
    element.classList.toggle('active');
    const content = element.nextElementSibling;
    content.classList.toggle('show');
}

// Edit episode
async function editEpisode(episodeId) {
    const response = await fetch(`/api/episodes/${episodeId}`);
    const episode = await response.json();
    currentEpisode = episode;
    
    document.getElementById('episode-list').style.display = 'none';
    document.getElementById('episode-edit').style.display = 'block';
    document.getElementById('episode-id').textContent = episode.episode_id;
    document.getElementById('episode_name').value = episode.episode_name;
    document.getElementById('season_number').value = episode.season || '';
    document.getElementById('episode_number').value = episode.episode_number;
    
    renderWordList(episode.words);
}

// Render word list for episode
function renderWordList(words) {
    const wordList = document.getElementById('word-list');
    wordList.innerHTML = `
        ${words.map(word => `
            <div class="word-item">
                <div class="word-header">
                    <input type="checkbox" 
                           onchange="toggleDefinitions('${word.word}')"
                           ${word.is_used ? 'checked' : ''}
                           id="word_use_${word.word}"
                           name="word_use_${word.word}">
                    <span id="word_text_${word.word}">${word.word}</span>
                    <input type="text" 
                           class="word-edit-box"
                           id="word_edit_${word.word}">
                    <a href="#" 
                       class="edit-link"
                       id="word_edit_link_${word.word}"
                       onclick="editWord('${word.word}'); return false;">edit</a>
                    ${word.original_form ? 
                        `<span class="original-form">(${word.original_form})</span>` : ''}
                </div>
                <div class="definitions" id="definitions_${word.word}">
                    ${word.definitions.map((def, idx) => `
                        <div class="definition-option">
                            <input type="radio" 
                                   name="word_definition_${word.word}"
                                   value="${def}"
                                   ${word.selected_definition === def ? 'checked' : ''}
                                   onchange="saveDefinitionSelection('${word.word}', '${def}')">
                            <label>${def}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('')}
        <div class="back-link-container">
            <a href="#" onclick="returnToEpisodeList(); return false;" class="back-link">Back to Episode List</a>
        </div>
    `;

    // Wait for the next tick to ensure DOM is updated
    setTimeout(() => {
        words.forEach(word => {
            if (word.is_used) {
                toggleDefinitions(word.word);
            }
            if (word.selected_definition) {
                selectedDefinitions[word.word] = word.selected_definition;
            }
        });
    }, 0);
}

// Return to episode list
async function returnToEpisodeList() {
    document.getElementById('episode-edit').style.display = 'none';
    document.getElementById('episode-list').style.display = 'block';
    
    // Re-render episode list to ensure it's up to date
    await renderEpisodesList();
    
    // Wait for DOM to update
    setTimeout(() => {
        // Expand the season of the episode we were just editing
        if (currentEpisode && currentEpisode.season !== null) {
            const seasonText = `Season ${currentEpisode.season || 'Unknown'}`;
            const seasonHeaders = document.querySelectorAll('.season-header');
            for (const header of seasonHeaders) {
                if (header.querySelector('span').textContent.trim() === seasonText) {
                    // Expand the season
                    if (!header.classList.contains('active')) {
                        toggleSeason(header);
                    }
                    // Scroll the season into view
                    header.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    break;
                }
            }
        }
    }, 100); // Give DOM time to update
}

// Toggle definitions visibility
function toggleDefinitions(word) {
    const checkbox = document.querySelector(`input[name="word_use_${word}"]`);
    const definitions = document.getElementById(`definitions_${word}`);
    
    if (!checkbox || !definitions) return;
    
    if (checkbox.checked) {
        definitions.classList.add('show');
        updateWordUse(word, true);
    } else {
        definitions.classList.remove('show');
        updateWordUse(word, false);
    }
}

// Save definition selection
async function saveDefinitionSelection(word, definition) {
    selectedDefinitions[word] = definition;
    await updateWordDefinition(word, definition);
}

// Edit word
function editWord(word) {
    const wordSpan = document.getElementById(`word_text_${word}`);
    const editBox = document.getElementById(`word_edit_${word}`);
    const editLink = document.getElementById(`word_edit_link_${word}`);

    if (!originalWords[word]) {
        originalWords[word] = wordSpan.textContent;
    }

    wordSpan.style.display = 'none';
    editBox.style.display = 'inline';
    editBox.value = wordSpan.textContent;
    editBox.focus();
    editLink.textContent = 'save';
    editLink.onclick = () => saveWord(word);

    editBox.onkeydown = (e) => {
        if (e.key === 'Escape') {
            cancelEdit(word);
        } else if (e.key === 'Enter') {
            saveWord(word);
        }
    };
}

// Save edited word
async function saveWord(word) {
    const wordSpan = document.getElementById(`word_text_${word}`);
    const editBox = document.getElementById(`word_edit_${word}`);
    const editLink = document.getElementById(`word_edit_link_${word}`);
    const newWord = editBox.value.trim();

    if (newWord && newWord !== word) {
        await updateWord(word, newWord);
        
        if (selectedDefinitions[word]) {
            selectedDefinitions[newWord] = selectedDefinitions[word];
            delete selectedDefinitions[word];
        }
    }

    wordSpan.textContent = newWord;
    wordSpan.style.display = 'inline';
    editBox.style.display = 'none';
    editLink.textContent = 'edit';
    editLink.onclick = () => editWord(newWord);
}

// Cancel word edit
function cancelEdit(word) {
    const wordSpan = document.getElementById(`word_text_${word}`);
    const editBox = document.getElementById(`word_edit_${word}`);
    const editLink = document.getElementById(`word_edit_link_${word}`);

    if (originalWords[word]) {
        wordSpan.textContent = originalWords[word];
        delete originalWords[word];
    }

    wordSpan.style.display = 'inline';
    editBox.style.display = 'none';
    editLink.textContent = 'edit';
    editLink.onclick = () => editWord(word);
}

// API calls
async function updateWord(oldWord, newWord) {
    const episodeId = document.getElementById('episode-id').textContent;
    await fetch(`/api/episodes/${episodeId}/words/${oldWord}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_word: newWord })
    });
}

async function updateWordUse(word, isUsed) {
    const episodeId = document.getElementById('episode-id').textContent;
    await fetch(`/api/episodes/${episodeId}/words/${word}/use`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_used: isUsed })
    });
}

async function updateWordDefinition(word, definition) {
    const episodeId = document.getElementById('episode-id').textContent;
    await fetch(`/api/episodes/${episodeId}/words/${word}/definition`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ definition: definition })
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', renderEpisodesList);
