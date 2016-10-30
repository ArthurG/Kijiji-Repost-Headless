import requests
import json
import bs4
import re
import sys

if sys.version_info < (3, 0):
    raise Exception("This program requires Python 3.0 or greater")

class KijijiApiException(Exception):
    def __init__(self, dump=None):
        if dump:
            with open('/tmp/kijiji-api-dump', 'w') as dumpfile:
                dumpfile.write(dump)
    def __str(self):
        return 'View /tmp/kijiji-api-dump/ for last dumpfile'

class SignInException(KijijiApiException):
    def __str__(self):
        return 'Could not sign in.\n'+super().__str__()

class PostAdException(KijijiApiException):
    def __str__(self):
        return 'Could not post ad.\n'+super().__str__()

class DeleteAdException(KijijiApiException):
    def __str__(self):
        return 'Could not delete ad.\n'+super().__str__()


#Retrive CSRF token from webpage
#Tokens are different every time a page is visitied. 
def getToken(html, tokenName):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    res = soup.select('[name='+tokenName+']')[0]
    return res['value']


class KijijiApi:
    #login:  user, password -> None (Sets session to logged in)
    #isLoggedIn: None -> bool
    #All function requires a logged in session to function correctly
    #logout: None -> None
    #postAd: None -> adId
    #deleteAd: adId -> None
    #getAllAds: None -> list(vector(adname, adId))

    def __init__(self):
        config = {}
        self.session = requests.Session()

    def login(self, username, password):
        url = 'http://www.kijiji.ca/h-kitchener-waterloo/1700212'
        resp = self.session.get(url)

        url = 'https://www.kijiji.ca/t-login.html'
        resp = self.session.get(url)

        payload = {'emailOrNickname': username,
                'password': password,
                'rememberMe': 'true',
                '_rememberMe': 'on',
                'ca.kijiji.xsrf.token': getToken(resp.text, 'ca.kijiji.xsrf.token'),
                'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
                }
        resp = self.session.post(url, data = payload)
        if not self.isLoggedIn():
            raise SignInException(resp.text)

    def isLoggedIn(self):
        indexPageText = self.session.get('https://www.kijiji.ca/m-my-ads.html/').text
        return 'm-logout.html' in indexPageText 

    def logout(self):
        resp = self.session.get('https://www.kijiji.ca/m-logout.html')

    def deleteAd(self, adId):
        myAdsPage = self.session.get('https://www.kijiji.ca/m-my-ads.html')

        params = {'Action': 'DELETE_ADS',
                'Mode': 'ACTIVE',
                'needsRedirect': 'false',
                'ads': '[{"adId":"'+adId+'","reason":"PREFER_NOT_TO_SAY","otherReason":""}]',
                'ca.kijiji.xsrf.token': getToken(myAdsPage.text, 'ca.kijiji.xsrf.token')
                }
        resp = self.session.post('https://www.kijiji.ca/j-delete-ad.json', data = params)
        if ("OK" not in resp.text):
            raise DeleteAdException(resp.text)

    def uploadImage(self, imageUrls=[],csv=""):
        #convert images from string and append them to the stuff to be uploaaded
        imageUrls.extend(csv.split(","))
        #Array to store images before they're returned
        uploadedImagesThumbnails = []

        imageUploadUrl = 'https://www.kijiji.ca/p-upload-image.html'
        for imageFile in imageUrls:
            files = {'file': open(imageFile, 'rb')}
            r = requests.post(imageUploadUrl, files = files)
            if (r.status_code != 200):
                raise PostAdException(r.text)
            imageTree = json.loads(r.text)
            imgUrl = imageTree['thumbnailUrl']
            uploadedImagesThumbnails.append(imgUrl)
        return uploadedImagesThumbnails

    def postAd(self, postVarsFile):
        resp = self.session.get('https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId=772')

        data = {}
        postVars = open(postVarsFile, 'rt')
        for line in postVars:
            [key, val] = line.lstrip().rstrip("\n").split("=")
            data[key] = val
        postVars.close()

        #Retrive tokens for website
        xsrfToken = getToken(resp.text, 'ca.kijiji.xsrf.token') 
        fraudToken = getToken(resp.text, 'postAdForm.fraudToken')
        data['ca.kijiji.xsrf.token']=xsrfToken
        data['postAdForm.fraudToken']=fraudToken

        #Upload the images
        imageList = self.uploadImage(csv=data['imageCsv'])
        data['images'] = ",".join(imageList)
        del data['imageCsv'] 

        #upload the ad itself
        newAdUrl="https://www.kijiji.ca/p-submit-ad.html"
        resp = self.session.post(newAdUrl, data=data)
        if (resp.status_code != 200 or \
                "message-container success" not in resp.text):
            raise PostAdException(resp.text)

        newCookieWithAdId = resp.headers['Set-Cookie']
        adId = re.search('\d+', newCookieWithAdId).group()
        return adId

    def getAllAds(self):
        myAdsUrl = 'http://www.kijiji.ca/j-get-my-ads.json'
        myAdsPage = self.session.get(myAdsUrl)
        myAdsTree = json.loads(myAdsPage.text) 
        adIds = [entry['id'] for entry in myAdsTree['myAdEntries']]
        adNames = [entry['title'] for entry in myAdsTree['myAdEntries']]
        return zip(adNames, adIds)

