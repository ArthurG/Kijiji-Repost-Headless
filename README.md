# KijijiBotV2
Automate Kijiji ad posting - Non-selenium version
###Send POST Requests to Kijiji... to post your ads

##Setup
- This project requires python3. 
- Required packages: python-requests, json, bs4, sqlalchemy
- I recommend using pip install to install these packages
- Generate a posting file (myAd.inf) by calling `python GenerateInfFile.py` and following the prompts
- Place all photo dependancies in the current directory
- start program by calling python KijijiCmd.py

#Requirements
-The program currently requires that you post at LEAST one photo
-As per Kijiji requirements, the item description must be at least 10 characters

##Usage

To post myAd.inf:

`python KijijiCmd.py -u (username) -p (password) post myAd.inf

To repost myAd.inf (Will delete the ad if it is already posted prior to posting):

`python KijijiCmd.py -u (username) -p (password) repost myAd.inf (or another inf file)`

To delete all ads:

`python KijijiCmd.py -u (username) -p (password) nuke `

To delete one ads:

`python KijijiCmd.py -u (username) -p (password) delete (adId)`

Alternatively, there are also interfaces for posting/reposting an ad from a folder. This makes it so you are not required to enter your username/password and may also be helpful if you choose to have multiple Kijiji accounts.
Inside your folder, include ALL photos, `item.inf`, and `login.inf`.
login.inf is as follows:
`username
password
`

To post from folder:

`python KijijiCmd.py folder (folderName)`

To repost from folder:

`python KijijiCmd.py repostFolder (folderName)`


##Issues
Please open a GitHub issue or pull request if you discover problems. 

##TODO 
- Error handling
- Modify GenerateInfFile to be more user friendly
- Interact with KijijiApi with a Facebook bot?!
