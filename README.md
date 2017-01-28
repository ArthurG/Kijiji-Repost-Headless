# KijijiBotV2
####Send POST requests to Kijiji... to post your ads

##Setup
- This project requires python3 with: python-requests, json, bs4, sqlalchemy
- run pip3 install -r requirements.txt

##Requirements
- The program currently requires that you post at LEAST one photo
- As per Kijiji requirements, the item description must be at least 10 characters

##Usage

###Generating a .inf file for an ad
- Generate a posting file (myAd.inf) with the command `python GenerateInfFile.py` and following the prompts
- Edit the location0 field in myAd.inf with correct value for your city. This can be found by doing an inspect element on the location dropdown on the Kijiji homepage and finding the the correct li#groupXXXXXXX for your city. 
- Place all photo dependancies in the current directory


###Posting + Reposting an ad
To post myAd.inf:

`python KijijiCmd.py -u (username) -p (password) post myAd.inf `

To repost myAd.inf (Will delete the ad if it is already posted prior to posting):

`python KijijiCmd.py -u (username) -p (password) repost myAd.inf (or another inf file)`

To delete all ads:

`python KijijiCmd.py -u (username) -p (password) nuke `

To delete one ads:

`python KijijiCmd.py -u (username) -p (password) delete (adId)`

Alternatively, there are also interfaces for posting/reposting an ad from a folder, especially useful if you're too lazy to enter your username/password every time or you have multiple Kijiji accounts.

Inside your folder, include ALL photos, `item.inf`, and `login.inf` which is as follows:

` username

password `

To post from folder:

`python KijijiCmd.py folder (folderName)`

To repost from folder:

`python KijijiCmd.py repostFolder (folderName)`


##Issues
Please open a GitHub issue or pull request if you discover problems. 

##TODO 
- Error handling -> automatically send bugs + logs to developer
- Modify GenerateInfFile to be more user friendly
- Organize files like a standard module
- Do some magic to avoid reuploading the same pictures again and again
