# KijijiBotV2
Automate Kijiji ad posting - Non-selenium version
###Send POST Requests to Kijiji... to post your ads

##Setup
- This project requires python3. 
- Required packages: python-requests, json, bs4, sqlalchemy
- I recommend using pip install to install these packages
- Generate a posting file (myAd.inf) by calling 'python GenerateInfFile.py'
- Place all photo dependancies in the current directory
- start program by calling python KijijiCmd.py

To Post an ad:

`python KijijiCmd.py post -u (username) -p (password) myAd.inf (or another inf file)`

To Repost an ad (delete ad if already posted):

`python KijijiCmd.py repost -u (username) -p (password) myAd.inf (or another inf file)`

To delete all ads:

`python KijijiCmd.py nuke -u (username) -p (password)`

To delete one ads:

`python KijijiCmd.py delete (adId) -u (username) -p (password)`

There are also interfaces for posting an ad from a folder:

`python KijijiCmd.py postFolder (folderName)`

Inside your folder, be sure to include all photos that you wish to upload as well, item.inf, login.inf (username + password on separate lines) and your photos

##Issues
This project is still in the works, there are likely bugs and problems. Please open a **GitHub issue** if you discover anything I should know. I will be glad to help!

##TODO 
- Error handling
- Modify GenerateInfFile to be more user friendly
- Interact with KijijiApi with a Facebook bot?!
