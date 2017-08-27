import requests
import json
import bs4
import re
import sys
from multiprocessing import Pool
from time import strftime

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")


class KijijiApiException(Exception):
    """
    Custom KijijiApi exception class
    """
    def __init__(self, dump=None):
        self.dumpfilepath = ""
        if dump:
            self.dumpfilepath = "kijiji_dump_{}.txt".format(strftime("%Y%m%dT%H%M%S"))
            with open(self.dumpfilepath, 'a') as f:
                f.write(dump)
    def __str__(self):
        if self.dumpfilepath:
            return "See {} in current directory for latest dumpfile.".format(self.dumpfilepath)
        else:
            return ""

class SignInException(KijijiApiException):
    def __str__(self):
        return "Could not sign in.\n"+super().__str__()

class PostAdException(KijijiApiException):
    def __str__(self):
        return "Could not post ad.\n"+super().__str__()

class BannedException(KijijiApiException):
    def __str__(self):
        return "Could not post ad, this user is banned.\n"+super().__str__()

class DeleteAdException(KijijiApiException):
    def __str__(self):
        return "Could not delete ad.\n"+super().__str__()


def get_token(html, token_name):
    """
    Retrive CSRF token from webpage
    Tokens are different every time a page is visitied
    """
    soup = bs4.BeautifulSoup(html, 'html.parser')
    res = soup.select("[name={}]".format(token_name))
    if not res:
        print("Token '{}' not found in html text.".format(token_name))
        return ""
    return res[0]['value']


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
        login_url = 'https://www.kijiji.ca/t-login.html'
        resp = self.session.get(login_url)
        payload = {
            'emailOrNickname': username,
            'password': password,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': get_token(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
        resp = self.session.post(login_url, data=payload)
        if not self.is_logged_in():
            raise SignInException(resp.text)

    def is_logged_in(self):
        """
        Return true if logged into Kijiji for the current session
        """
        index_page_text = self.session.get('https://www.kijiji.ca/m-my-ads.html/').text
        return "Sign Out" in index_page_text

    def logout(self):
        """
        Logout of Kijiji for the current session
        """
        self.session.get('https://www.kijiji.ca/m-logout.html')

    def delete_ad(self, ad_id):
        """
        Delete ad based on ad ID
        """
        my_ads_page = self.session.get('https://www.kijiji.ca/m-my-ads.html')
        params = {
            'Action': 'DELETE_ADS',
            'Mode': 'ACTIVE',
            'needsRedirect': 'false',
            'ads': '[{{"adId":"{}","reason":"PREFER_NOT_TO_SAY","otherReason":""}}]'.format(ad_id),
            'ca.kijiji.xsrf.token': get_token(my_ads_page.text, 'ca.kijiji.xsrf.token')
            }
        resp = self.session.post('https://www.kijiji.ca/j-delete-ad.json', data=params)
        if ("OK" not in resp.text):
            raise DeleteAdException(resp.text)

    def delete_ad_using_title(self, title):
        """
        Delete ad based on ad title
        """
        allAds = self.get_all_ads()
        [self.delete_ad(i) for t, i in allAds if t.strip() == title.strip()]

    def upload_image(self, token, image_files=[]):
        """
        Upload one or more photos to Kijiji concurrently using Pool

        'image_files' is a list of binary objects corresponding to images
        """
        image_urls = []
        image_upload_url = 'https://www.kijiji.ca/p-upload-image.html'
        for img_file in image_files:
            for i in range(0, 3):
                files = {'file': img_file}
                r = self.session.post(image_upload_url, files=files, headers={"x-ebay-box-token": token})
                if (r.status_code != 200):
                    print(r.status_code)
                try:
                    image_tree = json.loads(r.text)
                    img_url = image_tree['thumbnailUrl']
                    print("Image Upload success on try #{}".format(i+1))
                    image_urls.append(img_url)
                    break
                except (KeyError, ValueError) as e:
                    print("Image Upload failed on try #{}".format(i+1))
        return [image for image in image_urls if image is not None]

    def post_ad_using_data(self, data, image_files=[]):
        """
        Post new ad

        'data' is a dictionary of ad data that to be posted
        'image_files' is a list of binary objects corresponding to images to upload
        """
        # Load ad posting page
        resp = self.session.get('https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId=773')

        #Get tokens required for upload
        token_regex = r"initialXsrfToken: '\S+'"
        image_upload_token = re.findall(token_regex, resp.text)[0].strip("initialXsrfToken: '").strip("'")

        # Upload the images
        imageList = self.upload_image(image_upload_token, image_files)
        data['images'] = ",".join(imageList)

        # Retrive tokens for website
        data['ca.kijiji.xsrf.token'] = get_token(resp.text, 'ca.kijiji.xsrf.token')
        data['postAdForm.fraudToken'] = get_token(resp.text, 'postAdForm.fraudToken')
        data['postAdForm.description'] = data['postAdForm.description'].replace("\\n", "\n")

        # Upload the ad itself
        new_ad_url = "https://www.kijiji.ca/p-submit-ad.html"
        resp = self.session.post(new_ad_url, data=data)
        if not len(data.get("postAdForm.title", "")) >= 10:
            raise AssertionError("Your title is too short!")
        if (int(resp.status_code) != 200 or \
                "Delete Ad?" not in resp.text):
            if "There was an issue posting your ad, please contact Customer Service." in resp.text:
                raise BannedException(resp.text)
            else:
                raise PostAdException(resp.text)

        # Get adId and return it
        new_cookie_with_ad_id = resp.headers['Set-Cookie']
        ad_id = re.search('\d+', new_cookie_with_ad_id).group()
        return ad_id

    def get_all_ads(self):
        """
        Return an iterator of tuples containing the ad title and ad ID for every ad
        """
        resp = self.session.get('https://www.kijiji.ca/m-my-ads.html')
        user_id=get_token(resp.text, 'userId')
        my_ads_url = 'https://www.kijiji.ca/j-get-my-ads.json?_=1&currentOffset=0&isPromoting=false&show=ACTIVE&user={}'.format(user_id)
        my_ads_page = self.session.get(my_ads_url)
        my_ads_tree = json.loads(my_ads_page.text)
        ad_ids = [entry['id'] for entry in my_ads_tree['myAdEntries']]
        ad_names = [entry['title'] for entry in my_ads_tree['myAdEntries']]
        return zip(ad_names, ad_ids)
