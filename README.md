# TV Vocabulary Word Idenditfier

This project is to extract vocabulary words from transcripts of The Simpsons.

# Current Status
As of 1/5/2025:
- tv_vocab_bak.db is a copy of the database that doesn't store order of words appearing in episodes. It also stores the whole entry from wiktionary as the definition.
- wiktionary.db is most of wiktionary.xml but the script crashed about 70% of the way through

# Downloading Transcripts
Here is a good source of transcripts: https://www.springfieldspringfield.co.uk/episode_scripts.php?tv-show=the-simpsons

Transcripts are plain text ans stored in ./transcripts in the convetion of s<seacon number (2 digits)>e<episode number (2 digits)>

First, we need do download the transcripts. A good starting point is https://www.springfieldspringfield.co.uk/view_episode_scripts.php?tv-show=the-simpsons&episode=s01e01 grab the script from within the div with class "scrolling-script-container" and convert it from html to plain text. Get the episode from the URL (in this case s01e01) and save the file as ./transcripts/<episode>.txt Pause for a few seconds then get the URL from the a tag with the text "Next Episode" and repeat the process.

# Extracting Vocabulary Words

We will set up a SQLite database and collect words from the transcript in it. The database will have a table of words with the columns "word" and "count". It will join with a table of episodes to track which episode each word was seen in. The count column should have an index, so it is easy to get words that have are used infrequently.

A script will iterate the transcript files, extracting and lowercasing words and storing them in the database, adding the word if it is not already present, adding the episode if it is not already present, and incrementing the count for the word each time the word is encountered.

Once all the words are extracted and counted, we will determine if the extracted word is a vocabulary word. 

We want a local copy of wiktionary to query words and get definitions. We need to create a sqlite database to store all the words and parse the xml file to load into our database. The file is in wiktionary/dump.xml. It's a very large file, so we must use SAX to process it. We're looking for <page> elements that have a child <ns>0</ns>. We'll save the <title> element's text as the word, and use revision/text as the definition. We'll store the word and definition in the database.

A script will start at 1 and count up to 5. For each number, it will query the database for words that have been seen this number of times (and have an is_vocubulary value of NULL). For each of those words, it will query wiktionary to see i there is a definitions for that word. If there is, it will store the definition in the database and set is_vocabulary to TRUE. If not, it will store NULL for the definition and set is_vocabulary to FALSE. After it has done this for all words, it will move to the next number and repeat the process.
