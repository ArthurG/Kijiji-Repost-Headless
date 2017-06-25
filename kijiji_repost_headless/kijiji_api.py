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

class DeleteAdException(KijijiApiException):
    def __str__(self):
        return "Could not delete ad.\n"+super().__str__()


def get_token(html, tokenName):
    """
    Retrive CSRF token from webpage
    Tokens are different every time a page is visitied
    """
    soup = bs4.BeautifulSoup(html, 'html.parser')
    res = soup.select("[name={}]".format(tokenName))
    if not res:
        print("Token '{}' not found in html text.".format(tokenName))
        return ""
    return res[0]['value']

def upload_one_image(imgFile):
    """
    Try up to three times to upload the file
    If successful, return the url
    """
    imageUploadUrl = 'https://www.kijiji.ca/p-upload-image.html'
    for i in range(0, 3):
        files = {'file': imgFile}
        ses = requests.Session()
        r = ses.post(imageUploadUrl, files=files)
        if (r.status_code != 200):
            raise PostAdException(r.text)
        try:
            imageTree = json.loads(r.text)
            imgUrl = imageTree['thumbnailUrl']
            print("Image Upload success on try #{}".format(i+1))
            return imgUrl
        except KeyError as e:
            print("Image Upload failed on try #{}".format(i+1))
            pass
    return ""


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
        loginUrl = 'https://www.kijiji.ca/t-login.html'
        resp = self.session.get(loginUrl)
        payload = {
            'emailOrNickname': username,
            'password': password,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': get_token(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
        resp = self.session.post(loginUrl, data=payload)
        if not self.is_logged_in():
            raise SignInException(resp.text)

    def is_logged_in(self):
        """
        Return true if logged into Kijiji for the current session
        """
        indexPageText = self.session.get('https://www.kijiji.ca/m-my-ads.html/').text
        return "Sign Out" in indexPageText

    def logout(self):
        """
        Logout of Kijiji for the current session
        """
        self.session.get('https://www.kijiji.ca/m-logout.html')

    def delete_ad(self, adId):
        """
        Delete ad based on ad ID
        """
        myAdsPage = self.session.get('https://www.kijiji.ca/m-my-ads.html')
        params = {
            'Action': 'DELETE_ADS',
            'Mode': 'ACTIVE',
            'needsRedirect': 'false',
            'ads': '[{{"adId":"{}","reason":"PREFER_NOT_TO_SAY","otherReason":""}}]'.format(adId),
            'ca.kijiji.xsrf.token': get_token(myAdsPage.text, 'ca.kijiji.xsrf.token')
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

    def upload_image(self, imageFiles=[]):
        """
        Upload one or more photos to Kijiji concurrently using Pool

        'imageFiles' is a list of strings corresponding to image filenames
        """
        images = []
        with Pool(5) as p:
            images = p.map(upload_one_image, imageFiles)
        return [image for image in images if image is not None]

    def post_ad_using_data(self, data, imageFiles=[]):
        """
        Post new ad

        'data' is a dictionary of ad data that to be posted
        'imageFiles' is a list of strings corresponding to image filenames to upload
        """
        # Upload the images
        imageList = self.upload_image(imageFiles)
        data['images'] = ",".join(imageList)

        # Load ad posting page
        resp = self.session.get('https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId=773')

        # Retrive tokens for website
        data['ca.kijiji.xsrf.token'] = get_token(resp.text, 'ca.kijiji.xsrf.token')
        data['postAdForm.fraudToken'] = get_token(resp.text, 'postAdForm.fraudToken')

        # Upload the ad itself
        newAdUrl = "https://www.kijiji.ca/p-submit-ad.html"
        resp = self.session.post(newAdUrl, data=data)
        if not len(data.get("postAdForm.title", "")) >= 10:
            raise AssertionError("Your title is too short!")
        if (resp.status_code != 200 or \
                "message-container success" not in resp.text):
            raise PostAdException(resp.text)

        # Get adId and return it
        newCookieWithAdId = resp.headers['Set-Cookie']
        adId = re.search('\d+', newCookieWithAdId).group()
        return adId

    def get_all_ads(self):
        """
        Return an iterator of tuples containing the ad title and ad ID for every ad
        """
        resp = self.session.get('https://www.kijiji.ca/m-my-ads.html')
        userId=get_token(resp.text, 'userId')
        myAdsUrl = 'https://www.kijiji.ca/j-get-my-ads.json?_=1&currentOffset=0&isPromoting=false&show=ACTIVE&user={}'.format(userId)
        myAdsPage = self.session.get(myAdsUrl)
        myAdsTree = json.loads(myAdsPage.text)
        adIds = [entry['id'] for entry in myAdsTree['myAdEntries']]
        adNames = [entry['title'] for entry in myAdsTree['myAdEntries']]
        return zip(adNames, adIds)
