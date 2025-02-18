import sqlite3
import requests
import json
from tqdm import tqdm
import time
import os
import re
from utils.dictionary_utils import get_word_definitions

def get_context_from_transcript(episode_id, word):
    """
    Get the context around the word from the transcript file.
    Returns a window of text around the word occurrence.
    """
    # Find the transcript file
    transcript_dir = 'transcripts'
    transcript_file = os.path.join(transcript_dir, f"{episode_id}.txt")

    if not os.path.exists(transcript_file):
        print(f"Warning: Transcript file not found for episode {episode_id}")
        return None

    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the word in the content (case-insensitive)
        word_pattern = rf'\b{word}\b'
        match = re.search(word_pattern, content, re.IGNORECASE)

        if match:
            # Get a window of text around the word (e.g., 150 characters before and after)
            start = max(0, match.start() - 150)
            end = min(len(content), match.end() + 150)

            # Get the context and highlight the target word
            context = content[start:end]
            return context

    except Exception as e:
        print(f"Error reading transcript for episode {episode_id}: {str(e)}")

    return None

def get_best_definition(word, context, definitions):
    """
    Query Ollama API to select the best definition based on the context.
    """
    definitions_text = "\n".join(f"{i+1}. {def_}" for i, def_ in enumerate(definitions))

    prompt = f"""You are a language expert. Given the word "{word}" used in this context:
    "{context}"

    Choose the most appropriate definition from these options:
    {definitions_text}

    Rules:
    1. You MUST respond with ONLY a JSON object
    2. The JSON MUST have exactly one field: "definition_number"
    3. The value MUST be a number between 1 and {len(definitions)}
    4. You MUST NOT include any other text or explanation

    Example response: {{"definition_number": 1}}"""

    def try_get_definition(retry=False):
        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False
                })
            response.raise_for_status()
            result = response.json()
            response_text = result['response'].strip()

            try:
                response_json = json.loads(response_text)
                index = response_json.get('definition_number', 0) - 1
                if 0 <= index < len(definitions):
                    return definitions[index]
            except (ValueError, json.JSONDecodeError):
                pass

            if not retry:
                return try_get_definition(retry=True)
            print(f"Warning: Invalid definition number received for word '{word}': {response_text}")
            return None
        except Exception as e:
            print(f"Error getting best definition for word '{word}': {str(e)}")
            return None

    return try_get_definition()

def get_level_from_llm(word, definition, context):
    """
    Query Ollama API to determine the vocabulary level of a word.
    """
    prompt = f"""You are an educational expert. Given the word "{word}" with definition "{definition}" and usage context "{context}",
    classify it into one of these educational levels: elementary, middle, high, college, graduate, not vocabulary.

    Rules:
    1. You MUST respond with ONLY a JSON object
    2. The JSON MUST have exactly one field: "level"
    3. The value MUST be EXACTLY one of: "elementary", "middle", "high", "college", "graduate", "not vocabulary"
    4. Base your decision on:
       - Word complexity
       - Typical grade level of introduction
       - Academic usage
       - Subject matter relevance
    5. You MUST NOT include any other text or explanation
    6. You MUST NOT use any other values or variations

    Example response: {{"level": "elementary"}}"""

    def try_get_level(retry=False):
        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False
                })
            response.raise_for_status()
            result = response.json()
            response_text = result['response'].strip()

            try:
                response_json = json.loads(response_text)
                level = response_json.get('level', '').strip().lower()
                valid_levels = {'elementary', 'middle', 'high', 'college', 'graduate', 'not vocabulary'}
                if level in valid_levels:
                    return level
            except (ValueError, json.JSONDecodeError):
                pass

            if not retry:
                return try_get_level(retry=True)
            print(f"Warning: Invalid level received for word '{word}': {response_text}")
            return None
        except Exception as e:
            print(f"Error getting level for word '{word}': {str(e)}")
            return None

    return try_get_level()

def main():
    start_time = time.time()

    # Connect to the database
    conn = sqlite3.connect('db/tv_vocab.db')
    cursor = conn.cursor()

    # Get total count first
    cursor.execute('''
        SELECT COUNT(DISTINCT u.id)
        FROM uses u
        JOIN words w ON u.word = w.word
        WHERE w.is_vocabulary = 1
        AND u.level IS NULL
        AND u.no_definition = FALSE
    ''')
    total_remaining = cursor.fetchone()[0]

    # Get all uses that need level classification
    cursor.execute('''
        SELECT DISTINCT u.id, u.word, u.episode_id, u.original_word
        FROM uses u
        JOIN words w ON u.word = w.word
        WHERE w.is_vocabulary = 1
        AND u.level IS NULL
        AND u.no_definition = FALSE
        LIMIT 10000
    ''')

    records = cursor.fetchall()
    total = len(records)
    print(f"\nTotal records remaining to process: {total_remaining}")
    print(f"Processing batch of {total} records")

    # Initialize counters
    processed = 0
    skipped_no_def = 0
    skipped_no_context = 0
    skipped_no_best_def = 0
    skipped_no_level = 0
    successful = 0

    # Process each record
    pbar = tqdm(records, desc="Processing words", unit="word")
    for record in pbar:
        use_id, word, episode_id, original_word = record
        processed += 1

        # Get definitions from dictionary_utils
        definitions = get_word_definitions(word)
        if not definitions:
            skipped_no_def += 1
            # Update the no_definition flag
            try:
                cursor.execute('''
                    UPDATE uses
                    SET no_definition = TRUE
                    WHERE word = ?
                ''', (word,))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error updating no_definition flag for word '{word}': {str(e)}")
            pbar.set_postfix({"success": successful, "no_def": skipped_no_def, "no_ctx": skipped_no_context})
            continue

        # Get context from transcript
        context = get_context_from_transcript(episode_id, original_word)
        if not context:
            skipped_no_context += 1
            pbar.set_postfix({"success": successful, "no_def": skipped_no_def, "no_ctx": skipped_no_context})
            continue

        # Get best definition from LLM
        best_definition = get_best_definition(word, context, definitions)
        if not best_definition:
            skipped_no_best_def += 1
            pbar.set_postfix({"success": successful, "no_def": skipped_no_def, "no_ctx": skipped_no_context})
            continue

        # Get level from LLM
        level = get_level_from_llm(word, best_definition, context)
        if not level:
            skipped_no_level += 1
            pbar.set_postfix({"success": successful, "no_def": skipped_no_def, "no_ctx": skipped_no_context})
            continue

        try:
            cursor.execute('''
                UPDATE uses
                SET level = ?,
                    definition = ?
                WHERE id = ?
            ''', (level, best_definition, use_id))
            conn.commit()
            successful += 1
            pbar.set_postfix({"success": successful, "no_def": skipped_no_def, "no_ctx": skipped_no_context})
        except sqlite3.Error as e:
            print(f"Error updating database for word '{word}': {str(e)}")

    # Print final summary with timing information
    end_time = time.time()
    total_time = end_time - start_time
    successful_rate = successful / total if total > 0 else 0
    records_per_second = total / total_time
    estimated_total_time = total_remaining / records_per_second / 3600  # Convert to hours

    print("\nTiming Information:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per record: {total_time/total:.2f} seconds")
    print(f"Records processed per second: {records_per_second:.2f}")
    print(f"Success rate: {successful_rate*100:.1f}%")
    print(f"\nEstimated time to process remaining {total_remaining:,} records:")
    print(f"  {estimated_total_time:.1f} hours")
    print(f"  {estimated_total_time/24:.1f} days")

    print("\nProcessing Summary:")
    print(f"Total records processed: {processed}")
    print(f"Successfully updated: {successful}")
    print(f"Skipped (no definitions): {skipped_no_def}")
    print(f"Skipped (no context): {skipped_no_context}")
    print(f"Skipped (no best definition): {skipped_no_best_def}")
    print(f"Skipped (no level): {skipped_no_level}")

    # Print level distribution
    cursor.execute('''
        SELECT level, COUNT(*) as count
        FROM uses
        WHERE level IS NOT NULL
        GROUP BY level
        ORDER BY count DESC
    ''')
    print("\nLevel Distribution:")
    for level, count in cursor.fetchall():
        print(f"{level}: {count}")

    conn.close()

if __name__ == "__main__":
    main()
