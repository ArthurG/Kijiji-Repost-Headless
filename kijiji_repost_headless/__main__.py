import argparse
import os
import sys
from time import sleep

import kijiji_api
import generate_post_file as generator

import yaml

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")


def main():
    print("Note: A recent update has broken all previously generated .inf files. Please regenerate all your files - this script is not backwards compatible with previous versions. The commands are also changed. See README for details.")
    parser = argparse.ArgumentParser(description="Post ads on Kijiji")
    parser.add_argument('-u', '--username', help='username of your kijiji account')
    parser.add_argument('-p', '--password', help='password of your kijiji account')

    subparsers = parser.add_subparsers(help='sub-command help')

    post_parser = subparsers.add_parser('post', help='post a new ad')
    post_parser.add_argument('inf_file', type=str, help='.inf file containing posting details')
    post_parser.set_defaults(function=post_ad)

    show_parser = subparsers.add_parser('show', help='show currently listed ads')
    show_parser.set_defaults(function=show_ads)

    delete_parser = subparsers.add_parser('delete', help='delete a listed ad')
    delete_parser.add_argument('id', type=str, help='id of the ad you wish to delete')
    delete_parser.set_defaults(function=delete_ad)

    nuke_parser = subparsers.add_parser('nuke', help='delete all ads')
    nuke_parser.set_defaults(function=nuke)

    check_parser = subparsers.add_parser('check_ad', help='check if ad is active')
    check_parser.add_argument('folder_name', type=str, help='folder containing ad details')
    check_parser.set_defaults(function=check_ad)

    repost_parser = subparsers.add_parser('repost', help='repost an existing ad')
    repost_parser.add_argument('inf_file', type=str, help='.inf file containing posting details')
    repost_parser.set_defaults(function=repost_ad)

    build_parser = subparsers.add_parser('build_ad', help='Generates the item.kj_post file for a new ad')
    build_parser.set_defaults(function=generate_post_file)

    args = parser.parse_args()
    try:
        args.function(args)
    except AttributeError:
        parser.print_help()

def get_username_if_needed(args, data):
    if args.username is None or args.password is None:
        args.username = data["username"]
        args.password = data["password"]

def get_post_details(inf_file):
    """
    Extract ad data from inf file
    """
    with open(inf_file, 'rt') as infFileLines:
        #data = {key: val for line in infFileLines for (key, val) in (line.strip().split("="),)}
        data = yaml.load(infFileLines) 
        files = [open(os.path.join(os.path.dirname(inf_file), picture), 'rb').read() for picture in data['image_paths']]
    return [data, files]

def post_ad(args):
    """
    Post new ad
    """
    [data, image_files] = get_post_details(args.inf_file)
    get_username_if_needed(args, data)
    attempts = 1
    del data["username"]
    del data["password"]

    while not check_ad(args) and attempts < 5:
        if attempts > 1:
            print("Failed Attempt #{}, trying again.".format(attempts))
        attempts += 1
        api = kijiji_api.KijijiApi()
        api.login(args.username, args.password)
        api.post_ad_using_data(data, image_files)
    if not check_ad(args):
        print("Failed Attempt #{}, giving up.".format(attempts))


def show_ads(args):
    """
    Print list of all ads
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    [print("{} '{}'".format(ad_id, ad_name)) for ad_name, ad_id in api.get_all_ads()]


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

    [data, image_files] = get_post_details(args.inf_file)
    get_username_if_needed(args, data)

    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    del_ad_name = ""
    for item in data:
        if item[0] == "postAdForm.title":
            del_ad_name = item[0]
    try:
        api.delete_ad_using_title(del_ad_name)
        print("Existing ad deleted before reposting")
    except kijiji_api.DeleteAdException:
        print("Did not find an existing ad with matching title, skipping ad deletion")
        pass
    # Must wait a bit before posting the same ad even after deleting it, otherwise Kijiji will automatically remove it
    sleep(180)
    post_ad(args)

def check_ad(args):
    """
    Check if ad is live
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    ad_name = ""
    [data, image_files] = get_post_details(args.inf_file)
    for key, val in data.items():
        if key == "postAdForm.title":
            ad_name = val

    all_ads = api.get_all_ads()
    return [t for t, i in all_ads if t == ad_name]


def nuke(args):
    """
    Delete all ads
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    all_ads = api.get_all_ads()
    [api.delete_ad(ad_id) for ad_name, ad_id in all_ads]


def generate_post_file(args):
    generator.run_program()


if __name__ == "__main__":
    main()
