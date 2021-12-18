import json
import re
import sys
from time import strftime
from random import choice
import bs4
import requests
import yaml
import os

user_agents = [
    # Random list of top UAs for mac and windows/ chrome & FF
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/74.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/74.0"
]
session_ua = choice(user_agents)
request_headers = {"User-Agent": session_ua}

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")


class KijijiApiException(Exception):
    """
    Custom KijijiApi exception class
    """
    def __init__(self, msg="KijijiApi exception encountered.", dump=None):
        self.msg = msg
        self.dumpfilepath = ""
        if dump:
            self.dumpfilepath = "kijijiapi_dump_{}.html".format(strftime("%Y%m%dT%H%M%S"))
            with open(self.dumpfilepath, 'a', encoding='utf-8') as f:
                f.write(dump)

    def __str__(self):
        if self.dumpfilepath:
            return "{}\nSee {} in current directory for latest dumpfile.".format(self.msg, self.dumpfilepath)
        else:
            return self.msg


def get_token(html, attrib_name):
    """
    Return value of first match for element with name attribute
    """
    soup = bs4.BeautifulSoup(html, 'html.parser')
    res = soup.select("[name='{}']".format(attrib_name))
    if not res:
        raise KijijiApiException("Element with name attribute '{}' not found in html text.".format(attrib_name), html)
    return res[0]['value']


def get_kj_data(html):
    """
    Return dict of Kijiji page data
    The 'window.__data' JSON object contains many useful key/values
    """
    soup = bs4.BeautifulSoup(html, 'html.parser')
    p = re.compile(r'window\.__data=(.*);')
    script_list = soup.find_all("script", {"src": False})
    for script in script_list:
        if script:
            m = p.search(script.string)
            if m:
                return json.loads(m.group(1))
    raise KijijiApiException("'__data' JSON object not found in html text.", html)


def get_xsrf_token(html):
    """
    Return XSRF token
    This function is only necessary for the 'm-my-ads.html' page, as this particular page
    does not contain the usual 'ca.kijiji.xsrf.token' hidden HTML form input element, which is easier to scrape
    """
    soup = bs4.BeautifulSoup(html, 'html.parser')
    p = re.compile(r'Zoop\.init\(.*config: ({.+?}).*\);')
    for script in soup.find_all("script", {"src": False}):
        if script:
            m = p.search(script.string.replace("\n", ""))
            if m:
                # Using yaml to load since this is not valid JSON
                return yaml.load(m.group(1), Loader=yaml.FullLoader)['token']
    raise KijijiApiException("XSRF token not found in html text.", html)


class KijijiApi:
    """
    All functions require to be logged in to Kijiji first in order to function correctly
    """
    def __init__(self):
        config = {}
        self.session = requests.Session()

    def login(self, ssid):
        """
        Login to Kijiji for the current session
        """
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ssid_path = os.path.join(parent_dir, ssid)
        with open(ssid_path) as ssidFile:
            cookie_dict = {'ssid': ssidFile.read().strip()}
            requests.utils.add_dict_to_cookiejar(self.session.cookies, cookie_dict)

        if not self.is_logged_in():
            raise KijijiApiException("Could not log in.")

    def is_logged_in(self):
        """
        Return true if logged into Kijiji for the current session
        """
        resp = self.session.get('https://www.kijiji.ca/my/ads', headers=request_headers)
        try:
            resp.json()
            return True
        except:
            return False

    def logout(self):
        """
        Logout of Kijiji for the current session
        """
        self.session.get('https://www.kijiji.ca/m-logout.html',  headers=request_headers)

    def delete_ad(self, ad_id):
        """
        Delete ad based on ad ID
        """
        my_ads_page = self.session.get('https://www.kijiji.ca/m-my-ads.html',  headers=request_headers)
        token_head = self.session.head('https://www.kijiji.ca/j-token-gen.json',  headers=request_headers)
        xsrf_token = token_head.headers['X-Ebay-Box-Token']
        params = {
            'Action': 'DELETE_ADS',
            'Mode': 'ACTIVE',
            'needsRedirect': 'false',
            'ads': '[{{"adId":"{}","reason":"PREFER_NOT_TO_SAY","otherReason":""}}]'.format(ad_id),
            'ca.kijiji.xsrf.token': xsrf_token,
            'X-Ebay-Box-Token': xsrf_token,
        }
        resp = self.session.post('https://www.kijiji.ca/j-delete-ad.json', data=params,  headers=request_headers)
        if "OK" not in resp.text:
            raise KijijiApiException("Could not delete ad.", resp.text)

    def delete_ad_using_title(self, title):
        """
        Delete ad based on ad title
        """
        all_ads = self.get_all_ads()
        [self.delete_ad(ad['id']) for ad in all_ads if ad['title'].strip() == title.strip()]

    def upload_image(self, token, image_files=[]):
        """
        Upload one or more photos to Kijiji

        'image_files' is a list of binary objects corresponding to images
        """
        image_urls = []
        image_upload_url = 'https://www.kijiji.ca/p-upload-image.html'
        for img_file in image_files:
            for i in range(0, 3):
                r = self.session.post(
                    image_upload_url,
                    files={'file': img_file},
                    headers={
                        "X-Ebay-Box-Token": token,
                        "User-Agent": session_ua})
                r.raise_for_status()
                try:
                    image_tree = json.loads(r.text)
                    img_url = image_tree['thumbnailUrl']
                    print("Image upload success on try #{}".format(i+1))
                    image_urls.append(img_url)
                    break
                except (KeyError, ValueError):
                    print("Image upload failed on try #{}".format(i+1))
        return [image for image in image_urls if image is not None]

    def post_ad_using_data(self, data, image_files=[]):
        """
        Post new ad

        'data' is a dictionary of ad data that to be posted
        'image_files' is a list of binary objects corresponding to images to upload
        """
        # Load ad posting page (arbitrary category)
        resp = self.session.get('https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId=15', headers=request_headers)

        # Get token required for upload
        m = re.search(r"initialXsrfToken: '(\S+)'", resp.text)
        if m:
            image_upload_token = m.group(1)
        else:
            raise KijijiApiException("'initialXsrfToken' not found in html text.", resp.text)

        # Upload the images
        image_list = self.upload_image(image_upload_token, image_files)
        data['images'] = ",".join(image_list)

        # Retrieve XSRF tokens
        data['ca.kijiji.xsrf.token'] = get_token(resp.text, 'ca.kijiji.xsrf.token')
        data['postAdForm.fraudToken'] = get_token(resp.text, 'postAdForm.fraudToken')

        # Select basic package and confirm terms
        data['postAdForm.confirmedTerms'] = True
        data['featuresForm.featurePackage'] = "PKG_BASIC"

        # Format ad data and check constraints
        data['postAdForm.description'] = data['postAdForm.description'].replace("\\n", "\n")
        title_len = len(data.get("postAdForm.title", ""))
        if not title_len >= 8:
            raise KijijiApiException("Your ad title is too short! (min 8 chars)")
        if title_len > 64:
            raise KijijiApiException("Your ad title is too long! (max 64 chars)")

        # Upload the ad itself
        new_ad_url = "https://www.kijiji.ca/p-submit-ad.html"
        resp = self.session.post(new_ad_url, data=data, headers=request_headers)
        resp.raise_for_status()
        if "deleteSurveyReasons" not in resp.text:
            if "There was an issue posting your ad, please contact Customer Service." in resp.text:
                raise KijijiApiException("Could not post ad; this user is banned.", resp.text)
            else:
                raise KijijiApiException("Could not post ad.", resp.text)

        # Extract ad ID from response set-cookie
        ad_id = re.search('kjrva=(\d+)', resp.headers['Set-Cookie']).group(1)

        return ad_id

    def get_all_ads(self):
        """
        Return a list of dicts with properties for every active ad
        """
        resp = self.session.get('https://www.kijiji.ca/my/ads', headers=request_headers)
        resp.raise_for_status()
        ads_json = json.loads(resp.text)
        ads_info = ads_json['ads']

        if ads_info:
            # Get rank (ie. page number) for each ad
            # Can't use dict comprehension for building params because every key has the same name,
            # must use a list of key-value tuples instead
            params = [("ids", ad['id']) for ad in ads_info.values()]
            resp = self.session.get('https://www.kijiji.ca/my/ranks', params=params, headers=request_headers)
            resp.raise_for_status()
            ranks_json = json.loads(resp.text)

            # Add ranks to existing ad properties dict
            for ad_id, rank in ranks_json['ranks'].items():
                ads_info[ad_id]['rank'] = rank

        return [ad for ad in ads_info.values()]
