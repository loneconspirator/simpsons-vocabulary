# The Simpsons Vocabulary Builder

This project extracts and presents vocabulary words from transcripts of The Simpsons TV show, creating an interactive web page for learning new words.

_Vibe Coded to get a decent vocabulary site up quick, because I want it to exist_

## Features

- **Interactive Web Interface**: Browse vocabulary by season and episode
- **Vocabulary Level Indicators**: Words are categorized by difficulty level (Elementary, Middle School, High School, College, Graduate)
- **Wiktionary Integration**: Words link directly to their Wiktionary definitions
- **Shareable Links**: URLs include query parameters for sharing specific episodes
- **Responsive Design**: Clean layout with Simpsons-inspired color scheme

## Project Structure

- `transcripts/`: Contains plain text transcripts of episodes (format: `s01e01.txt`)
- `web/`: Output directory for the generated HTML interface
- `9_build_web_page.py`: Main script that generates the interactive HTML page

## Current Status

The project currently:
- Extracts vocabulary words from Simpsons transcripts
- Categorizes words by difficulty level
- Generates an interactive web page with season and episode navigation
- Links words to their Wiktionary definitions
- Supports shareable URLs with query parameters

## Usage

1. Do some stuff like set up a venv and install requirements
1. Run all the scripts to set up the database
1. Run the web page generator:
   ```
   python 9_build_web_page.py
   ```
1. Open `web/index.html` in your browser to view the vocabulary interface
1. Navigate using the Season and Episode buttons, or use URL parameters (e.g., `index.html?season=1&episode=3`)

## Data Sources

- Transcripts: [Springfield! Springfield!](https://www.springfieldspringfield.co.uk/episode_scripts.php?tv-show=the-simpsons)
- Definitions: [Wiktionary](https://www.wiktionary.org/)
