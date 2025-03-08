import csv
import openai
import time
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# CSV file to read from
csv_file = '../output/output.csv'

# Function to get the vocabulary level from OpenAI
def get_vocabulary_level(word, definition):
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
                You are an education expert, specializing in language arts.
                Determine the vocabulary level of a given word based on its definition.
                Possible levels are: elementary, middle, high, college.

                - Reply "elementary" if the word might be a more challenging word in books written for fourth or fifth graders.
                - Reply "middle" for words that would be among the more challenging words that appear in books taught to sixth, seventh, and eight graders.
                - Say "high" for challenging words in books taught to ninth, tenth, eleventh, and twelfth graders.
                - Say "college" for words more challenging than any other level.
                - Say "not vocabulary" if the word is too common, uninteresting, or unchallenging to be used as a vocabulary word.

                Respond with only one word from the specified list of levels or "not vocabulary".
                """},
                {"role": "user", "content": f"Word: {word}\nDefinition: {definition}\nLevel: "}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting vocabulary level for {word}: {e}")
        return None

# Read the CSV file and process the specified number of records
def process_csv(num_records):
    with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile, open('../output/new_levels.csv', 'w', newline='', encoding='utf-8') as output_csv:
        reader = csv.DictReader(csvfile)
        fieldnames = ['id', 'episode_id', 'word', 'level']
        writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
        writer.writeheader()

        processed_count = 0
        for row in reader:
            # if processed_count >= num_records:
            #     break

            word = row['word']
            definition = row['definition']

            level = get_vocabulary_level(word, definition)
            writer.writerow({
                'id': row['id'],
                'episode_id': row['episode_id'],
                'word': word,
                'level': level
            })
            time.sleep(1)

            processed_count += 1

# Example usage: process the first 10 records
if __name__ == "__main__":
    num_records_to_process = 100  # Change this to the desired number of records
    process_csv(num_records_to_process)
