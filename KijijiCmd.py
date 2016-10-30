import requests
import json
import bs4
import re
from ReallySecurePasswordModule import username, password 
import argparse
import KijijiApi


def main():
   ##Start here 
   #Takes: config(user/pass)
   #One of:
   #post adPostingFile
   #show
   #delete adId
   #showPresentAds adId
   #repost adPostingFile
   parser = argparse.ArgumentParser(
           description="Post ads on Kijiji")
   parser.add_argument('username', help='username of your kijiji account')
   parser.add_argument('password', help='password of your kijiji account')

   subparsers = parser.add_subparsers(help ='sub-command help')
   
   postParser = subparsers.add_parser('post', help='post a new ad')
   postParser.add_argument('inf_file', type=str, help='.inf file containing posting details')
   postParser.set_defaults(function=postAd)

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
   except AttributeError:
        parser.print_help()

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

def nuke(args):
    api = KijijiApi.KijijiApi()
    api.login(args.username, args.password)
    allAds = api.getAllAds()
    [api.deleteAd(adId) for adName, adId in allAds]

if __name__ == "__main__":
    main()
