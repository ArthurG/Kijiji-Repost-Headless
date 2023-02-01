import json
import re
import argparse
import os
import sys
import logging
import time
from time import sleep
from bs4 import BeautifulSoup
import datetime
import random
from pathlib import Path
from kijiji_repost_headless import kijiji_api

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")


def main():
    parser = argparse.ArgumentParser(description="Repost ads on Kijiji by backing up all active ads, deleting, "
                                                 "and reposting from backup. Requires input directory with a"
                                                 " `.accounts.json` file that has list of emails and passwords "
                                                 "for the accounts to repost."
                                                 ""
                                                 "File should have structure: "
                                                 "{ 'accounts': { ['username': 'ipsum', 'pass': 'gipsum']}}")
    parser.add_argument('-d', '--dir', help='backup directory for kijiji ads', default='$HOME/kijiji')

    args = parser.parse_args()
    # print(args.username)
    try:
        full_repost(args)
    except argparse.ArgumentError:
        parser.print_help()


def process_account(account: dict, work_dir: str):
    # get username:
    user_account = account.get('username', None)
    if not user_account:
        raise ValueError("Usename missing for account")
    user = user_account.split('@')[0]
    passwd = account.get('pass', None)
    if not passwd:
        raise ValueError(f"Password missing for account {user}")
    date = datetime.datetime.now().astimezone().strftime('%Y-%m-%d_%H-%M-%S')
    # parse backup directory
    backup_dir = os.path.join(work_dir, user)
    if not os.path.isdir(backup_dir):
        # try to create the dir
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        prev_backups = []
    else:
        # get all previous backups:
        dir_items = os.listdir(backup_dir)
        date_matches = [re.match(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', k) for k in dir_items]
        prev_backups = []
        for k in date_matches:
            if k:
                prev_backups.append(os.path.join(backup_dir, k[0]))
        # sorts from oldest [0] to newest [-1]
        prev_backups.sort()

    def load_backup_ads(backup_dir: str) -> dict:
        loaded_ads = {}
        files_in_backup_dir = os.listdir(backup_dir)
        backed_up_files = [k for k in files_in_backup_dir if k.endswith('.xml')]

        for ad in backed_up_files:
            ad_path = os.path.join(backup_dir, ad)
            with open(ad_path, 'rb') as f:
                ad_bytes = f.read()
                soup = BeautifulSoup(str(ad_bytes), 'html.parser')
                ad_title = soup.find('ad:title').text
                ad_title = ad_title.replace("\\", "")  # removes any odd characters
                loaded_ads[ad_title] = (ad_path, ad_bytes)

        return loaded_ads

    if prev_backups:
        last_backup_ads = load_backup_ads(prev_backups[-1])

    # log in
    api = kijiji_api.KijijiApi()
    api.login(user_account, passwd)
    time.sleep(0.5)
    if not api.is_logged_in():
        raise ValueError("Could not log in")
    # first, get all ads currently up:
    active_ads = api.get_all_ads()

    # TODO: check for change between active ads and last_backup_ads
    # are there NEW Ads? are some not there?

    # create new backup dir:
    backup_subdir = os.path.join(backup_dir, date)
    if not os.path.isdir(backup_subdir):
        Path(backup_subdir).mkdir(parents=True, exist_ok=True)
    else:
        raise ValueError("this backup already exits...")

    # back up all ads
    for ad in active_ads:
        ad_bytes = api.scrape_ad(ad)
        pre_filter_name = re.sub(r'([\/:?!^@#&$%,"”~<>\-`;_=(){}\[\]\\* ])', '_', ad['ad:title'])
        write_name = re.sub(r'(\_+)', '_', pre_filter_name)
        with open(os.path.join(backup_subdir, write_name + ".xml"), 'wb') as f:
            f.write(ad_bytes)

    # validate all ads were backed up:
    ads_in_backup = [str(k) for k in Path(backup_subdir).rglob('*.xml')]
    if len(ads_in_backup) != len(active_ads):
        raise ValueError("Not all ads backed up")

    # validate that all ads were deleted:
    attempts = 0
    while len(active_ads) > 0:
        # now delete all adds with some random jitter so Kijiji API isn't hit too hard...
        for ad in active_ads:
            api.delete_ad(ad['@id'])
            sleep(5 + 5 * random.random())
        attempts += 1
        active_ads = api.get_all_ads()
        if active_ads:
            print("Not all ads deleted, trying again!")
        else:
            print(f"All ads deleted in {attempts} attempts, waiting for 30s")
            # sleep to let kijiji update its db
            time.sleep(60)
        if attempts > 10:
            raise ValueError("Attempted to delete all ads 10 times, but no luck.")


    # now repost from backup
    files_in_backup_dir = os.listdir(backup_subdir)
    backed_up_files = [k for k in files_in_backup_dir if k.endswith('.xml')]

    for ad in backed_up_files:
        ad_path = os.path.join(backup_subdir, ad)
        with open(ad_path, 'rb') as f:
            ad_bytes = f.read()
            soup = BeautifulSoup(str(ad_bytes), 'html.parser')
            ad_title = soup.find('ad:title').text
            ad_title = ad_title.replace("\\", "")  # removes any odd characters
            logger.info("Posting ad: {}".format(ad_title))
            api.post_ad_using_data(ad_bytes)
            sleep(5 + 5 * random.random())

    sleep(5)
    active_ads = api.get_all_ads()
    if len(active_ads) != len(backed_up_files):
        raise ValueError("didn't repost all :/")


def full_repost(args):
    # get accounts info from .accounts.json file in the root directory:
    if not os.path.isfile(os.path.join(args.dir, '.accounts.json')):
        raise FileNotFoundError(f"Could not find .accounts.json file in {args.dir}")
    with open(os.path.join(args.dir, '.accounts.json'), 'r') as f:
        accounts_raw = json.load(f)
    accounts = accounts_raw.get('accounts', None)
    for account in accounts[-1:]:
        process_account(account=account, work_dir=args.dir)


if __name__ == "__main__":
    main()
