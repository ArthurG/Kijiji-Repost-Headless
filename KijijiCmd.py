import argparse
import KijijiApi
import sys

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")

def main():
   ##Start here 
   #Takes: config(user/pass)
   #One of:
   #post adPostingFile
   #show
   #delete adId
   #show
   #repost adPostingFile
   parser = argparse.ArgumentParser(
           description="Post ads on Kijiji")
   parser.add_argument('-u', '--username', help='username of your kijiji account')
   parser.add_argument('-p', '--password', help='password of your kijiji account')

   subparsers = parser.add_subparsers(help ='sub-command help')
   
   postParser = subparsers.add_parser('post', help='post a new ad')
   postParser.add_argument('inf_file', type=str, help='.inf file containing posting details')
   postParser.set_defaults(function=postAd)

   folderParser = subparsers.add_parser('folder', help='post ad from folder')
   folderParser.add_argument('folderName', type=str, help='folder containing ad details')
   folderParser.set_defaults(function=postFolder)

   repostFolderParser = subparsers.add_parser('repostFolder', help='post ad from folder')
   repostFolderParser.add_argument('folderName', type=str, help='folder containing ad details')
   repostFolderParser.set_defaults(function=repostFolder)
   
   showParser = subparsers.add_parser('show', help='show currently listed ads')
   showParser.set_defaults(function=showAds)

   deleteParser = subparsers.add_parser('delete', help='delete a listed ad')
   deleteParser.add_argument('id',type=str, help='id of the ad you wish to delete')
   deleteParser.set_defaults(function=deleteAd)

   nukeParser = subparsers.add_parser('nuke', help='delete all ads')
   nukeParser.set_defaults(function=nuke)

   repostParser = subparsers.add_parser('repost', help='repost an existing ad')
   repostParser.add_argument('inf_file', type = str,help = '.inf file containing posting details')
   repostParser.set_defaults(function=repostAd)

   args = parser.parse_args()
   try:
       args.function(args)
   except AttributeError as err:
       parser.print_help()

def postFolder(args):
    api = KijijiApi.KijijiApi()
    api.postFolder(args.folderName)

def postAd(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    api.postAd(args.inf_file)

def showAds(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    [print(adId+","+adName) for adName, adId in api.getAllAds()]

def deleteAd(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    api.deleteAd(args.id)

#Try to delete ad with same name if possible
#post new ad
def repostAd(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    myAds = api.getAllAds()
    delAdName = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
        if key =='postAdForm.title':
            delAdName = val
    try:
        [api.deleteAd(adId) for adName, adId in api.getAllAds() if delAdName.strip() == adName]
    except DeleteAdException:
        pass
    api.postAd(args.inf_file)

def repostFolder(args):
    #TODO: Function isn't working
    api = KijijiApi.KijijiApi()
    api.postFolder(args.folderName)

def nuke(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    allAds = api.getAllAds()
    [api.deleteAd(adId) for adName, adId in allAds]

if __name__ == "__main__":
    main()
