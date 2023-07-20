# MusicBrainz Bot

This bot adds links to the [Discography of American Historical Recordings](https://adp.library.ucsb.edu/) 
to artists in [MusicBrainz](https://musicbrainz.org/). MusicBrainz artists are matched to DAHR entries based on a 
MusicBrainz link's presence in the Wikidata page that has been determined (via LC-NAF) to match a DAHR entry.


## Overview
- `editing.py` - Contains a class `MusicBrainzClient` for interacting with MusicBrainz. Based on previous bot, but much narrower functionality & using selenium web driver instead of mechanize (switched to handle info on pages loaded in via javascript)
- `run_bot.py` - Handles loading/saving progress and running the editing loop over the input DAHR data.
- `config.ini` - Configuration variables used by the bot.
- `requirements.txt` - Required packages.

## Usage
Install requirements using e.g. `pip install -r requirements.txt`

Update `config.ini` file (see below)

Run using: `python3 runbot.py`

## Configuration
```
[musicbrainz]
server = <musicbrainz server to run on, e.g. test.musicbrainz.org>
username = <bot username>
password = <bot password>

[dahr]
input_csv = <csv of input data containing DAHR IDs & MusicBrainz IDs>
dahr_id_field = <field name in above CSV for DAHR ID>
mb_id_field = <field name in above CSV for MusicBrainz ID>

[general]
headless = <False to run without visible browser, True to run with visible browser>
checked_file = <path to json file for saving which entries have been checked>
modified_file = <path to json file for saving which entries have been modified>
error_file = <path to json file for saving errors>
log = <path to .log file for saving bot logs>
save_interval = <integer number of entries to do before saving>
edit_note = <message to be included in the Edit Note section of each edit>
```

