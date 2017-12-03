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

    post_parser = subparsers.add_parser('post', help='post a new ad')
    post_parser.add_argument('inf_file', type=str, help='.inf file containing posting details')
    post_parser.set_defaults(function=post_ad)

    folder_parser = subparsers.add_parser('folder', help='post ad from folder')
    folder_parser.add_argument('folder_name', type=str, help='folder containing ad details')
    folder_parser.set_defaults(function=post_folder)

    repost_folder_parser = subparsers.add_parser('repost_folder', help='post ad from folder')
    repost_folder_parser.add_argument('folder_name', type=str, help='folder containing ad details')
    repost_folder_parser.set_defaults(function=repost_folder)

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

    build_parser = subparsers.add_parser('build_ad', help='Generates the item.inf file for a new ad')
    build_parser.set_defaults(function=generate_inf_file)

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
    cred_file = args.folder_name + "/login.inf"
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
    os.chdir(args.folder_name)
    post_ad(args)


def post_ad(args):
    """
    Post new ad
    """
    [data, image_files] = get_inf_details(args.inf_file)
    attempts = 1
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
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    del_ad_name = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
        if key == "postAdForm.title":
            del_ad_name = val
    try:
        api.delete_ad_using_title(del_ad_name)
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
    os.chdir(args.folder_name)
    repost_ad(args)


def check_ad(args):
    """
    Check if ad is live
    """
    api = kijiji_api.KijijiApi()
    api.login(args.username, args.password)
    ad_name = ""
    for line in open(args.inf_file, 'rt'):
        [key, val] = line.strip().rstrip("\n").split("=")
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


def generate_inf_file(args):
    generator.run_program()


if __name__ == "__main__":
    main()
