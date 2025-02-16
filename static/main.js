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
        <div class="word-list-header">
            <h2>Vocabulary Words</h2>
            <div class="word-list-actions">
                <div class="add-word-form">
                    <input type="text" 
                           id="new-word-input" 
                           placeholder="Add new word..."
                           onkeydown="if (event.key === 'Enter') addNewWord()">
                    <button onclick="addNewWord()">Add</button>
                </div>
                <a href="#" onclick="showAllWords(); return false;" class="show-all-link">Show All Words</a>
            </div>
        </div>
        <div class="word-items-container">
            ${words.map((word, index) => `
                <div class="word-item" 
                     data-word="${word.word}"
                     data-order="${index + 1}"
                     ondragover="handleDragOver(event)"
                     ondrop="handleDrop(event)">
                    <div class="word-header">
                        <div class="drag-handle"
                             draggable="true"
                             ondragstart="handleDragStart(event)"
                             ondragend="handleDragEnd(event)">⋮⋮</div>
                        <input type="checkbox" 
                               onchange="handleWordUseChange(event, '${word.word}')"
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
                           onclick="editWord('${word.word}', event); return false;">edit</a>
                        ${word.original_form && word.original_form !== word.word ? 
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
                        <div class="definition-option custom-definition">
                            <input type="radio" 
                                   name="word_definition_${word.word}"
                                   value="custom"
                                   ${word.selected_definition && !word.definitions.includes(word.selected_definition) ? 'checked' : ''}>
                            <textarea class="custom-definition-input"
                                    id="custom_definition_${word.word}"
                                    placeholder="Enter custom definition..."
                                    onfocus="handleCustomDefinitionFocus(event, '${word.word}')"
                                    onblur="handleCustomDefinitionBlur(event, '${word.word}')">${word.selected_definition && !word.definitions.includes(word.selected_definition) ? word.selected_definition : ''}</textarea>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        <div class="back-link-container">
            <a href="#" onclick="returnToEpisodeList(); return false;" class="back-link">Back to Episode List</a>
        </div>
    `;

    // Wait for the next tick to ensure DOM is updated
    setTimeout(() => {
        words.forEach(word => {
            if (word.is_used) {
                toggleDefinitionsVisibility(word.word, true);
            }
            if (word.selected_definition) {
                selectedDefinitions[word.word] = word.selected_definition;
            }
        });
    }, 0);
}

// Toggle definitions visibility without updating use status
function toggleDefinitionsVisibility(word, show) {
    const definitions = document.getElementById(`definitions_${word}`);
    if (definitions) {
        if (show) {
            definitions.classList.add('show');
        } else {
            definitions.classList.remove('show');
        }
    }
}

// Handle checkbox change
function handleWordUseChange(event, word) {
    const isChecked = event.target.checked;
    toggleDefinitionsVisibility(word, isChecked);
    updateWordUse(word, isChecked);
}

// Drag and drop handlers
let draggedItem = null;
let isDragging = false;

function handleDragStart(event) {
    isDragging = true;
    // Get the word-item parent, not just the handle
    draggedItem = event.target.closest('.word-item');
    event.dataTransfer.effectAllowed = 'move';
    draggedItem.classList.add('dragging');
}

function handleDragOver(event) {
    if (!isDragging) return;
    event.preventDefault();
    
    const wordItem = event.target.closest('.word-item');
    if (!wordItem || wordItem === draggedItem) return;
    
    const rect = wordItem.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    
    // Just update visual indicators
    if (event.clientY < midpoint) {
        wordItem.classList.add('drag-above');
        wordItem.classList.remove('drag-below');
    } else {
        wordItem.classList.add('drag-below');
        wordItem.classList.remove('drag-above');
    }
}

async function handleDrop(event) {
    if (!isDragging) return;
    event.preventDefault();
    
    const wordItem = event.target.closest('.word-item');
    if (!wordItem || !draggedItem || wordItem === draggedItem) return;
    
    // Remove drag indicators
    document.querySelectorAll('.drag-above, .drag-below').forEach(el => {
        el.classList.remove('drag-above', 'drag-below');
    });
    draggedItem.classList.remove('dragging');
    
    const container = wordItem.parentNode;
    
    // Determine if we're dropping above or below the target
    const rect = wordItem.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    const dropAfter = event.clientY > midpoint;
    
    // Move the dragged item to its new position
    if (dropAfter) {
        wordItem.insertAdjacentElement('afterend', draggedItem);
    } else {
        wordItem.insertAdjacentElement('beforebegin', draggedItem);
    }
    
    // Only update orders once after the drop is complete
    await updateWordOrders(container);
    isDragging = false;
}

function handleDragEnd(event) {
    if (!isDragging) return;
    
    document.querySelectorAll('.drag-above, .drag-below').forEach(el => {
        el.classList.remove('drag-above', 'drag-below');
    });
    
    if (draggedItem) {
        draggedItem.classList.remove('dragging');
        draggedItem = null;
    }
    isDragging = false;
}

// Separate function to update word orders
async function updateWordOrders(container) {
    const wordOrders = Array.from(container.children).map((item, index) => ({
        word: item.dataset.word,
        order: index + 1
    }));
    
    try {
        const response = await fetch(`/api/episodes/${currentEpisode.episode_id}/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ wordOrders })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update word order');
        }
    } catch (error) {
        console.error('Error updating word order:', error);
        // Revert the UI change on error
        const episode = await fetch(`/api/episodes/${currentEpisode.episode_id}`).then(r => r.json());
        renderWordList(episode.words);
    }
}

// Add a new word
async function addNewWord() {
    const input = document.getElementById('new-word-input');
    const word = input.value.trim();
    
    if (!word) return;
    
    try {
        const response = await fetch(`/api/episodes/${currentEpisode.episode_id}/uses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ word })
        });
        
        if (!response.ok) {
            throw new Error('Failed to add word');
        }
        
        const wordData = await response.json();
        
        // Add the new word to the current episode's word list
        const episode = await fetch(`/api/episodes/${currentEpisode.episode_id}`).then(r => r.json());
        renderWordList(episode.words);
        
        // Clear the input
        input.value = '';
        
    } catch (error) {
        console.error('Error adding word:', error);
        alert('Failed to add word. Please try again.');
    }
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

// Save definition selection
async function saveDefinitionSelection(word, definition) {
    selectedDefinitions[word] = definition;
    await updateWordDefinition(word, definition);
}

// Edit word
function editWord(word, event) {
    if (event) event.preventDefault();
    
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
    editLink.onclick = (e) => saveWord(word, e);

    editBox.onkeydown = (e) => {
        if (e.key === 'Escape') {
            cancelEdit(word);
        } else if (e.key === 'Enter') {
            saveWord(word);
        }
    };
}

// Save edited word
async function saveWord(word, event) {
    if (event) event.preventDefault();
    
    const wordSpan = document.getElementById(`word_text_${word}`);
    const editBox = document.getElementById(`word_edit_${word}`);
    const editLink = document.getElementById(`word_edit_link_${word}`);
    const newWord = editBox.value.trim();

    if (newWord && newWord !== word) {
        // Update the word in the backend
        await updateWord(word, newWord);
        
        // Update selected definitions if they exist
        if (selectedDefinitions[word]) {
            selectedDefinitions[newWord] = selectedDefinitions[word];
            delete selectedDefinitions[word];
        }

        // Update all DOM elements with the new word
        const wordItem = wordSpan.closest('.word-item');
        
        // Update checkbox
        const checkbox = wordItem.querySelector(`input[name="word_use_${word}"]`);
        if (checkbox) {
            checkbox.name = `word_use_${newWord}`;
            checkbox.id = `word_use_${newWord}`;
            checkbox.onchange = () => handleWordUseChange(event, newWord);
        }
        
        // Update word span
        wordSpan.id = `word_text_${newWord}`;
        wordSpan.textContent = newWord;
        
        // Update edit box
        editBox.id = `word_edit_${newWord}`;
        
        // Update edit link
        editLink.id = `word_edit_link_${newWord}`;
        editLink.onclick = (e) => editWord(newWord, e);
        
        // Update definitions container if it exists
        const definitions = wordItem.querySelector(`#definitions_${word}`);
        if (definitions) {
            definitions.id = `definitions_${newWord}`;
            
            // Update radio buttons in definitions
            const radios = definitions.querySelectorAll('input[type="radio"]');
            radios.forEach(radio => {
                radio.name = `word_definition_${newWord}`;
                radio.onchange = () => saveDefinitionSelection(newWord, radio.value);
            });
        }
    }

    wordSpan.style.display = 'inline';
    editBox.style.display = 'none';
    editLink.textContent = 'edit';
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

// Show all words in episode
async function showAllWords() {
    const response = await fetch(`/api/episodes/${currentEpisode.episode_id}/all-words`);
    const words = await response.json();
    
    const wordList = document.getElementById('word-list');
    wordList.innerHTML = `
        <div class="word-list-header">
            <h2>All Words</h2>
            <a href="#" onclick="showVocabularyWords(); return false;" class="show-vocab-link">Show Vocabulary Only</a>
        </div>
        <div class="word-table">
            <table>
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Used</th>
                        <th>Vocabulary</th>
                        <th>Original Form</th>
                    </tr>
                </thead>
                <tbody>
                    ${words.map(word => `
                        <tr>
                            <td>${word.word}</td>
                            <td>
                                <input type="checkbox" 
                                       onchange="toggleWordUse('${word.word}', this.checked)"
                                       ${word.is_used ? 'checked' : ''}>
                            </td>
                            <td>
                                <input type="checkbox" 
                                       onchange="toggleWordVocabulary('${word.word}', this.checked)"
                                       ${word.is_vocabulary ? 'checked' : ''}>
                            </td>
                            <td>${word.original_form !== word.word ? word.original_form : ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="back-link-container">
            <a href="#" onclick="returnToEpisodeList(); return false;" class="back-link">Back to Episode List</a>
        </div>
    `;
}

// Show vocabulary words only
async function showVocabularyWords() {
    const response = await fetch(`/api/episodes/${currentEpisode.episode_id}`);
    const episode = await response.json();
    renderWordList(episode.words);
}

// Toggle word vocabulary status
async function toggleWordVocabulary(word, isVocabulary) {
    await fetch(`/api/words/${word}/vocabulary`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_vocabulary: isVocabulary })
    });
}

// Handle custom definition focus
function handleCustomDefinitionFocus(event, word) {
    // Select the associated radio button when the text area is focused
    const radio = event.target.parentElement.querySelector('input[type="radio"]');
    radio.checked = true;
}

// Handle custom definition blur
async function handleCustomDefinitionBlur(event, word) {
    const customDefinition = event.target.value.trim();
    if (customDefinition) {
        // Only save if there's actually a definition entered
        const radio = event.target.parentElement.querySelector('input[type="radio"]');
        if (radio.checked) {
            await saveDefinitionSelection(word, customDefinition);
        }
    }
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
