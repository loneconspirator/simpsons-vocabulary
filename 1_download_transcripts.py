import os
import time
import requests
from bs4 import BeautifulSoup

def clean_text(text):
    """Clean the transcript text by removing extra whitespace and normalizing line endings."""
    return ' '.join(text.split())

def download_transcript(url):
    """Download and extract transcript from the given URL."""
    response = requests.get(url)
    if response.status_code != 200:
        return None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    script_container = soup.find('div', class_='scrolling-script-container')
    
    if not script_container:
        return None, None
    
    # Extract episode code from URL
    episode = url.split('episode=')[1]
    transcript = clean_text(script_container.get_text())
    
    # Find next episode link
    next_link = soup.find('a', text='Next Episode')
    next_url = None
    if next_link:
        next_url = next_link['href']
        if next_url.startswith('/'):
            next_url = 'https://www.springfieldspringfield.co.uk' + next_url
    
    return episode, transcript, next_url

def main():
    # Create transcripts directory if it doesn't exist
    os.makedirs('./transcripts', exist_ok=True)
    
    # Start with the first episode
    current_url = 'https://www.springfieldspringfield.co.uk/view_episode_scripts.php?tv-show=the-simpsons&episode=s26e04'
    
    while current_url:
        print(f"Downloading transcript from: {current_url}")
        
        episode, transcript, next_url = download_transcript(current_url)
        
        if episode and transcript:
            # Save transcript to file
            filename = f"./transcripts/{episode}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"Saved transcript to {filename}")
        else:
            print(f"Failed to download transcript from {current_url}")
        
        # Update URL for next episode
        current_url = next_url
        
        # Pause to be nice to the server
        time.sleep(3)
        
if __name__ == "__main__":
    main()
