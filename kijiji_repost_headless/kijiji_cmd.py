import argparse
import os
import sys
from time import sleep

import kijiji_api

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
   postParser.set_defaults(function=post_ad)

   folderParser = subparsers.add_parser('folder', help='post ad from folder')
   folderParser.add_argument('folderName', type=str, help='folder containing ad details')
   folderParser.set_defaults(function=post_folder)

   repostFolderParser = subparsers.add_parser('repost_folder', help='post ad from folder')
   repostFolderParser.add_argument('folderName', type=str, help='folder containing ad details')
   repostFolderParser.set_defaults(function=repost_folder)
   
   showParser = subparsers.add_parser('show', help='show currently listed ads')
   showParser.set_defaults(function=show_ads)

   deleteParser = subparsers.add_parser('delete', help='delete a listed ad')
   deleteParser.add_argument('id',type=str, help='id of the ad you wish to delete')
   deleteParser.set_defaults(function=delete_ad)

   nukeParser = subparsers.add_parser('nuke', help='delete all ads')
   nukeParser.set_defaults(function=nuke)

   repostParser = subparsers.add_parser('repost', help='repost an existing ad')
   repostParser.add_argument('inf_file', type = str,help = '.inf file containing posting details')
   repostParser.set_defaults(function=repost_ad)

   args = parser.parse_args()
   #try:
   args.function(args)
   #except AttributeError as err:
    #   print(err)
    #   parser.print_help()

#HELPER FUNCTIONS
def get_folder_data(args):
    args.inf_file = "item.inf"
    cred_file = args.folderName+"/login.inf"
    f = open(cred_file, 'r')
    creds = [line.strip() for line in f]
    args.username = creds[0] 
    args.password = creds[1] 

def get_inf_details(inf_file):
    data = {}
    infFileLines = open(inf_file, 'rt')
    data={}
    for line in infFileLines:
        [key, val] = line.lstrip().rstrip("\n").split("=")
        data[key] = val
    infFileLines.close()
    
    ##open picture files
    files=[]
    for picture in data['imageCsv'].split(","):
        f = open(picture, 'rb').read()
        files.append(f)
    return [data, files]

##Actual Functions called from main
def post_folder(args):
    get_folder_data(args)
    os.chdir(args.folderName)
    post_ad(args)

def post_ad(args):
    [data, imageFiles] = get_inf_details(args.inf_file)
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    api.post_ad_using_data(data, imageFiles)

def show_ads(args):
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    [print("{} '{}'".format(adId, adName)) for adName, adId in api.get_all_ads()]

def delete_ad(args):
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    api.delete_ad(args.id)

def delete_ad_using_title(name):
    api = kijiji_api.KijijiApi()
    api.delete_ad_using_title(name)

#Try to delete ad with same name if possible
#post new ad
def repost_ad(args):
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    delAdName = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
        if key =='postAdForm.title':
            delAdName = val
    try:
        api.delete_ad_using_title(delAdName)
        print("Existing ad deleted before reposting")
    except kijiji_api.DeleteAdException:
        print("Did not find an existing ad with matching title, skipping ad deletion")
        pass
    # Must wait a bit before posting the same ad even after deleting it, otherwise Kijiji will automatically remove it
    sleep(180)
    post_ad(args)

def repost_folder(args):
    get_folder_data(args)
    os.chdir(args.folderName)
    repost_ad(args)

def nuke(args):
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    allAds = api.get_all_ads()
    [api.delete_ad(adId) for adName, adId in allAds]

if __name__ == "__main__":

    main()
