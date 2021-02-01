# Kijiji Repost Headless

[![Build Status](https://circleci.com/gh/ArthurG/Kijiji-Repost-Headless.svg?style=svg)](https://circleci.com/gh/ArthurG/Kijiji-Repost-Headless)

#### Post ads on Kijiji

## Setup

- This project requires python3 with: python-requests, bs4, pyyaml
- Run `pip3 install -r requirements.txt` to install all dependencies
- Insure you have fzf and sxiv installed `apt-get install fzf sxiv`

## Requirements

- The program currently requires that you post at LEAST one photo
- As per Kijiji requirements, the item description must be at least 10 characters

## Usage

### Getting your SSID

Before posting an ad, you will need to manually get your Kijiji SSID.

1. Log into Kijiji in your browser. Make sure "remember me" is checked.
2. Inspect the cookies that have been set by Kijiji for your browser.
3. Find the cookie named "ssid" and copy its value.
4. Paste the value into the "ssid.txt" file.
5. Alternately use export cookies addon in your browser (when on kijiji page and logged in and run this command to extract:

`cat cookies.txt | grep ssid | awk '{print $NF}' > ssid.txt`

### Generating an ad posting file

- Generate a posting file (item.yml) with the command `python kijiji_repost_headless build_ad` and follow the prompts
- Place all photo dependencies in the path RELATIVE to item.yml 
- It is recommended that you create separate folders for each ad that you wish to post and include item.yml and photos in the same directory

### Posting and Reposting an ad

Post one ad (item.yml):

`python kijiji_repost_headless [-s ssid_file] post myproduct/item.yml`

Repost one ad (item.yml); will delete the ad prior to posting if it already exists:

`python kijiji_repost_headless [-s ssid_file] repost myproduct/item.yml`

Show all active ads:

`python kijiji_repost_headless [-s ssid_file] show`

Delete all ads:

`python kijiji_repost_headless [-s ssid_file] nuke`

Delete one ad (using ad id):

`python kijiji_repost_headless [-s ssid_file] delete myAdId`

## Project Structure

```
project
│   README.md
│   LICENSE
│   requirements.txt
│
└───kijiji_repost_headless
│   │   kijiji_api.py -> Interfaces with Kijiji
│   │   generate_post_file.py -> Makes item.yml
│   │   get_ids -> Used for retreiving kijiji location data
│   │   kijiji_categories_attr.json -> Finds out what properties each item has
│   │   kijiji_categories_attr.json -> Finds out what properties each item has
│   │   save_attribute_map_to_json.py -> Remakes kijiji_categories_attr.json
│   │   __main__.py -> Wraps kijiji_api.py for ease of use from command line, file is run when 'python kijiji_repost_headless' is run
│   │
└───tests
```

## Issues

Please open a GitHub issue or pull request if you discover problems.

## TODO

- Better error handling
- Avoid reuploading the same pictures again and again
