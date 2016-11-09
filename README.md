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

##Usage

To Post an ad:

`python KijijiCmd.py post -u (username) -p (password) myAd.inf (or another inf file)`

To Repost an ad (delete ad if already posted):

`python KijijiCmd.py repost -u (username) -p (password) myAd.inf (or another inf file)`

To delete all ads:

`python KijijiCmd.py nuke -u (username) -p (password)`

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
This project is still in the works, there are likely bugs and problems. Please open a **GitHub issue** if you discover anything I should fix. I will be glad to help!

##TODO 
- Error handling
- Modify GenerateInfFile to be more user friendly
- Interact with KijijiApi with a Facebook bot?!
