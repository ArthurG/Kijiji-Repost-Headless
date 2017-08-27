import argparse
import os
import sys
from time import sleep

import kijiji_api
import generate_inf_file as generator

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")


def main():
    parser = argparse.ArgumentParser(description="Post ads on Kijiji")
    parser.add_argument('-u', '--username', help='username of your kijiji account')
    parser.add_argument('-p', '--password', help='password of your kijiji account')

    subparsers = parser.add_subparsers(help='sub-command help')

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
    deleteParser.add_argument('id', type=str, help='id of the ad you wish to delete')
    deleteParser.set_defaults(function=delete_ad)

    nukeParser = subparsers.add_parser('nuke', help='delete all ads')
    nukeParser.set_defaults(function=nuke)

    checkParser = subparsers.add_parser('check_ad', help='check if ad is active')
    checkParser.add_argument('folderName', type=str, help='folder containing ad details')
    checkParser.set_defaults(function=check_ad)

    repostParser = subparsers.add_parser('repost', help='repost an existing ad')
    repostParser.add_argument('inf_file', type=str, help='.inf file containing posting details')
    repostParser.set_defaults(function=repost_ad)

    buildParser = subparsers.add_parser('build_ad', help='Generates the item.inf file for a new ad')
    buildParser.set_defaults(function=generate_inf_file)

    args = parser.parse_args()
    try:
        args.function(args)
    except AttributeError:
        parser.print_help()


def get_folder_data(args):
    """
    Set ad data inf file and extract login credentials from inf files
    """
    args.inf_file = "item.inf"
    cred_file = args.folderName + "/login.inf"
    creds = [line.strip() for line in open(cred_file, 'r')]
    args.username = creds[0]
    args.password = creds[1]


def get_inf_details(inf_file):
    """
    Extract ad data from inf file
    """
    with open(inf_file, 'rt') as infFileLines:
        data = {key: val for line in infFileLines for (key, val) in (line.strip().split("="),)}
    files = [open(picture, 'rb').read() for picture in data['imageCsv'].split(",")]
    return [data, files]


def post_folder(args):
    """
    Post new ad from folder
    """
    get_folder_data(args)
    os.chdir(args.folderName)
    post_ad(args)


def post_ad(args):
    """
    Post new ad
    """
    [data, imageFiles] = get_inf_details(args.inf_file)
    attempts = 1
    while not check_ad(args) and attempts < 5:
        if attempts > 1:
            print("Failed Attempt #" + str(attempts) + ", trying again.")
        attempts += 1
        api = kijiji_api.KijijiApi()
        api.login(args.username, args.password)
        api.post_ad_using_data(data, imageFiles)
        sleep(180)
    if not check_ad(args):
        print("Failed Attempt #" + str(attempts) + ", giving up.")


def show_ads(args):
    """
    Print list of all ads
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    [print("{} '{}'".format(adId, adName)) for adName, adId in api.get_all_ads()]


def delete_ad(args):
    """
    Delete ad
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    api.delete_ad(args.id)


def delete_ad_using_title(name):
    """
    Delete ad based on ad title
    """
    api = kijiji_api.KijijiApi()
    api.delete_ad_using_title(name)


def repost_ad(args):
    """
    Repost ad

    Try to delete ad with same title if possible before reposting new ad
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    delAdName = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
        if key == "postAdForm.title":
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
    """
    Repost ad from folder
    """
    get_folder_data(args)
    os.chdir(args.folderName)
    repost_ad(args)


def check_ad(args):
    """
    Check if ad is live
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    AdName = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
        if key == "postAdForm.title":
            AdName = val
    allAds = api.get_all_ads()
    return [t for t, i in allAds if t == AdName]


def nuke(args):
    """
    Delete all ads
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    allAds = api.get_all_ads()
    [api.delete_ad(adId) for adName, adId in allAds]

def generate_inf_file(args):
    generator.run_program()

if __name__ == "__main__":
    main()
