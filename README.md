# Kijiji Repost Headless

#### Send  POST requests to Kijiji... to post your ads

## Setup
- This project requires python3 with: python-requests, bs4
- Run `pip3 install -r requirements.txt`

## Requirements
- The program currently requires that you post at LEAST one photo
- As per Kijiji requirements, the item description must be at least 10 characters

## Usage

### Generating a .inf file for an ad
- Generate a posting file (item.inf) with the command `python kijiji_repost_headless build_ad` and follow the prompts
- Place all photo dependancies in the path RELATIVE to item.kj_post 
- It is recommended that you create folders for each item that you wish to post, and include item.kj_post and photos in that directory

### Posting + Reposting an ad
To post item.kj_post:

`python kijiji_repost_headless -u (username) -p (password) post myproduct/item.kj_post`

To repost item.kj_post (will delete the ad if it is already posted prior to posting):

`python kijiji_repost_headless -u (username) -p (password) repost myproduct/item.kj_post`

To delete all ads:

`python  kijiji_repost_headless -u (username) -p (password) nuke`

To delete one ad:

`python kijiji_repost_headless -u (username) -p (password) delete (adId)`

## Project Structure

```
project
│   README.md
│   LICENSE
│   requirements.txt    
│
└───kijiji_repost_headless
│   │   kijiji_api.py -> Interfaces with Kijiji
│   │   generate_post_file.py -> Makes item.kj_post
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
- Error handling -> automatically send bugs + logs to developer
- Avoid reuploading the same pictures again and again

