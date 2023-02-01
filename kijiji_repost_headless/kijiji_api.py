import json
import sys
from time import strftime
import requests
import yaml
import os
import xmltodict
import time

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

class KijijiApi:
    """
    All functions require to be logged in to Kijiji first in order to function correctly
    """
    def __init__(self):
        config = {}
        self.session = requests.Session()

    def login(self, username, password):
        """
        Login to Kijiji for the current session
        """

        url = "https://mingle.kijiji.ca/api/users/login"
        headers = {
			"content-type":"application/x-www-form-urlencoded",
			"accept":"*/*",
			"x-ecg-ver":"1.67",
			"x-ecg-ab-test-group":"",
			"accept-language":"en-CA",
			"accept-encoding":"gzip",
			"user-agent":"Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)"
        }

        payload = {"username": username, "password":password, "socialAutoRegistration": "false"}

        r = self.session.post(url, headers = headers, data = payload)

        # if kijiji response valid attempt to parse response
        if r.status_code == 200 and r.text != "":
            parsed = xmltodict.parse(r.text)
            self.userID = parsed["user:user-logins"]["user:user-login"]["user:id"]
            self.userToken = parsed["user:user-logins"]["user:user-login"]["user:token"]
            self.email = username
        else:
            raise KijijiApiException("Could not log in.")

        if not self.is_logged_in():
            raise KijijiApiException("Could not log in.")

    def is_logged_in(self):
        """
        Return true if logged into Kijiji for the current session
        """

        url = 'https://mingle.kijiji.ca/api/locations'
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers = {
            'accept':'*/*',
            'x-ecg-ver':'1.67',
            'x-ecg-authorization-user': userAuth,
            'x-ecg-ab-test-group':'',
            'user-agent':'Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)',
            'accept-language':'en-CA',
            'accept-encoding':'gzip'
        }

        r = self.session.get(url, headers = headers)
        return r.status_code == 200 and r.text != ''

    def logout(self):
        # Broken
        """
        Logout of Kijiji for the current session
        """
        self.session.get('https://www.kijiji.ca/m-logout.html',  headers=request_headers)

    def delete_ad(self, ad_id):
        """
        Delete ad based on ad ID
        """
        url = 'https://mingle.kijiji.ca/api/users/{}/ads/{}'.format(self.userID, ad_id)
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers = {
            "content-type":"application/xml",
            "x-ecg-ver":"1.67",
            "x-ecg-ab-test-group":"",
            "x-ecg-authorization-user": userAuth,
            "accept-encoding": "gzip",
            "user-agent":"Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)"
        }

        r = self.session.delete(url, headers = headers)

        if r.status_code == 204:
            print('Ad ' + ad_id + ' Successfully Deleted')
            return True
        else:
            raise KijijiApiException("Could not delete ad.")

    def delete_ad_using_title(self, title):
        # Broken
        """
        Delete ad based on ad title
        """
        all_ads = self.get_all_ads()
        [self.delete_ad(ad['id']) for ad in all_ads if ad['title'].strip() == title.strip()]

    def upload_image(self, token, image_files=[]):
        # Broken
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
        # missing images
        url = 'https://mingle.kijiji.ca/api/users/{}/ads'.format(self.userID)
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers={
            'content-type':'application/xml',
            'accept':'*/*',
            'x-ecg-ver':'1.67',
            'x-ecg-ab-test-group':'',
            'accept-encoding': 'gzip',
            'x-ecg-authorization-user': userAuth,
            'accept-language':'en-CA',
            'user-agent':'Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)'
        }
        r = self.session.post(url, headers=headers, data=data)
        
        if r.status_code == 201 and r.text != '':
            parsed = xmltodict.parse(r.text)
            return True
        else:
            return False


    def scrape_ad(self, old_ad_details):
        details = {
            '@xmlns:types': 'http://www.ebayclassifiedsgroup.com/schema/types/v1', 
            '@xmlns:cat': 'http://www.ebayclassifiedsgroup.com/schema/category/v1', 
            '@xmlns:loc': 'http://www.ebayclassifiedsgroup.com/schema/location/v1', 
            '@xmlns:ad': 'http://www.ebayclassifiedsgroup.com/schema/ad/v1', 
            '@xmlns:attr': 'http://www.ebayclassifiedsgroup.com/schema/attribute/v1', 
            '@xmlns:pic': 'http://www.ebayclassifiedsgroup.com/schema/picture/v1', 
            '@xmlns:user': 'http://www.ebayclassifiedsgroup.com/schema/user/v1', 
            '@xmlns:rate': 'http://www.ebayclassifiedsgroup.com/schema/rate/v1', 
            '@xmlns:reply': 'http://www.ebayclassifiedsgroup.com/schema/reply/v1', 
            '@locale': 'en-CA'
        }

        attribute_paths = [
            ["ad:title"], 
            ["ad:description"], 
            ["loc:locations", "loc:location", "@id"], 
            ["ad:ad-type", "ad:value"], 
            ["cat:category", "@id"], 
            ["ad:ad-address", "types:zip-code"], 
            ["ad:ad-address", "types:full-address"], 
            ["ad:price", "types:price-type", "types:value"], 
            ["ad:price", "types:amount"], 
            ["pic:pictures", "pic:picture"], 
            ["attr:attributes"]
        ]

        for path in attribute_paths:
            curr_dict_dest = details
            curr_dict_src = old_ad_details
            for k in path[:-1]:
                if k in curr_dict_src and curr_dict_src != "" and curr_dict_src != None:
                   curr_dict_src = curr_dict_src[k]

                   if k not in curr_dict_dest:
                       curr_dict_dest[k] = {}
                   curr_dict_dest = curr_dict_dest[k]
                else:
                    curr_dict_dest = {}
                    break
            if curr_dict_src is not None and path[-1] in curr_dict_src:
                curr_dict_dest[path[-1]] = curr_dict_src[path[-1]]
        
        details["ad:email"] = self.email
        details = {'ad:ad': details }
        ad_final = xmltodict.unparse(details, short_empty_elements=True, pretty=True)
        return ad_final.encode("utf-8")

    def getAttributes(self, attributeID):
        url = 'https://mingle.kijiji.ca/api/ads/metadata/{}'.format(attributeID)
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers = {
            'accept':'*/*',
            'x-ecg-ver':'1.67',
            'x-ecg-authorization-user': userAuth,
            'x-ecg-ab-test-group':'',
            'user-agent':'Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)',
            'accept-language':'en-CA',
            'accept-encoding':'gzip'
            }

        r = self.session.get(url, headers = headers)

        if r.status_code == 200 and r.text != '':
            print(r.text)
            parsed = xmltodict.parse(r.text)
            return parsed
        else:
            parsed = xmltodict.parse(r.text)
            print(parsed)
    
    def get_categories(self):
        url = 'https://mingle.kijiji.ca/api/categories'
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers = {
            'accept':'*/*',
            'x-ecg-ver':'1.67',
            'x-ecg-authorization-user': userAuth,
            'x-ecg-ab-test-group':'',
            'user-agent':'Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)',
            'accept-language':'en-CA',
            'accept-encoding':'gzip'
            }

        r = self.session.get(url, headers = headers)
        
        if r.status_code == 200 and r.text != '':
            parsed = xmltodict.parse(r.text)
            print(parsed)
            return parsed
        else:
            parsed = xmltodict.parse(r.text)
            print(parsed)

        pass


    def _get_paginated_ads(self, url: str, headers: dict) -> list:

        ads = []
        r = self.session.get(url, headers=headers)

        if r.status_code == 200 and r.text != '':
            parsed = xmltodict.parse(r.text)
            # no ads case
            if ("ad:ad" not in parsed["ad:ads"]):
                return []

            ads_from_request = parsed["ad:ads"]["ad:ad"]

            # Single ad case
            if "@id" in ads:
                ads = [ads_from_request]
            # multi ad case
            else:
                ads = ads_from_request

            # find out if there is next token:
            links = parsed['ad:ads']['types:paging']['types:link']
            if '@href' in links:
                return ads
            else:
                # there are more ads
                for link in links:
                    if link['@rel'] == 'next':
                        nextPage = link['@href']
                        time.sleep(0.5)
                        ads += self._get_paginated_ads(url=nextPage, headers=headers)

        return ads

    def get_all_ads(self):
        """
        Return a list of dicts with properties for every active ad
        """
        url = 'https://mingle.kijiji.ca/api/users/{}/ads?page=0&size=100'.format(self.userID)
        userAuth = 'id="{}", token="{}"'.format(self.userID, self.userToken)
        headers = {
            'accept':'*/*',
            'x-ecg-ver':'1.67',
            'x-ecg-authorization-user': userAuth,
            'x-ecg-ab-test-group':'',
            'user-agent':'Kijiji 12.15.0 (iPhone; iOS 13.5.1; en_CA)',
            'accept-language':'en-CA',
            'accept-encoding':'gzip'
            }
        # use paginator to capture ads on multiple pages:
        return self._get_paginated_ads(url=url, headers=headers)

