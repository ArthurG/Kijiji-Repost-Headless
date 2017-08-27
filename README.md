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
- Place all photo dependancies in the current directory

### Posting + Reposting an ad
Make sure you're in the ROOT directory of the project before proceeding!

To post item.inf:

`python kijiji_repost_headless -u (username) -p (password) post item.inf`

To repost item.inf (will delete the ad if it is already posted prior to posting):

`python kijiji_repost_headless -u (username) -p (password) repost item.inf`

To delete all ads:

`python  kijiji_repost_headless -u (username) -p (password) nuke`

To delete one ad:

`python kijiji_repost_headless -u (username) -p (password) delete (adId)`

Alternatively, there are also commands for posting/reposting an ad from a folder, which is especially useful for saving you from re-entering your username/password 

Inside your folder, include ALL photos, an `item.inf` ad file, and a `login.inf` file with the first line containing your Kijiji login email and the second line containing your Kijiji login password.

To post from folder:

`python kijiji_repost_headless folder (folderName)`

To repost from folder:

`python kijiji_repost_headless repost_folder (folderName)`

## Project Structure

```
project
│   README.md
│   LICENSE
│   requirements.txt    
│
└───kijiji_repost_headless
│   │   kijiji_api.py -> Interfaces with Kijiji
│   │   generate_inf_file.py -> Makes item.inf
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

