import requests
import json
import bs4
import re
from ReallySecurePasswordModule import username, password 
import argparse

#Fn looks through the HTML to find a token with required name
#Tokens are different every time a page is visitied. 
#These tokens are usedc to 'prevent' bots
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
        self.session.post('https://www.kijiji.ca/j-delete-ad.json', data = params)

    def uploadImage(self, imageUrls=[],csv=""):
        #convert images from string and append them to the stuff to be uploaaded
        imageUrls.extend(csv.split(","))
        #Array to store images before they're returned
        uploadedImagesThumbnails = []

        imageUploadUrl = 'https://www.kijiji.ca/p-upload-image.html'
        for imageFile in imageUrls:
            files = {'file': open(imageFile, 'rb')}
            r = requests.post(imageUploadUrl, files = files)
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
        f = open("myAd.html", "w")
        f.write(resp.text)
        f.close()

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
   parser.add_argument('email',  type=str,
           help='the email of your kijiji account')
   parser.add_argument('password', type=str,
           help='the password of your kijiji account')
   subparsers = parser.add_subparsers(help ='sub-command help')
   
   postParser = subparsers.add_parser('post', help='post a new ad')
   postParser.add_argument('inf file', type=str, help='.inf file containing posting details')
   postParser.set_defaults(func=post_ad)
   
   showParser = subparsers.add_parser('show', help='show currently listed ads')
   showParser.set_defaults(func=post_ad)

   deleteParser = subparsers.add_parser('delete', help='delete a listed ad')
   deleteParser.add_argument('id',type=str, help='id of the ad you wish to delete')
   deleteParser.set_defaults(func=show_ads)

   nukeParser = subparsers.add_parser('nuke', help='delete all listed ads')
   nukeParser.set_defaults(func=delete_all)

   repostParser = subparsers.add_parser('repost', help='repost an existing ad')
   repostParser.add_argument('inf file', type=str, help='.inf file containing posting details')
   repostParser.set_defaults(func=repost_ad)
   
   #repostParser = subparsers.add_parser('repost', help='repost an existing ad')
   #repostParser = repostParser.add_argument('inf_file',  help = '.inf file containing posting details')
   #repostParser.set_defaults(func=repost_ad)

   args = parser.parse_args()
   args.func(args)

def post_ad(args):
    print(args)
    print("Hi!")

def show_ads(args):
    print("Hi!")

def delete(args):
    print("Hi")

def nuke(args):
    print("nuking")

def repost_ad(args):
    print("Hi!")


#Try to delete ad with same name if possible
#post new ad
def repostAd(ad_all):
    
    print("Hi!")

def main2():
    api = KijijiApi()
    print(api.isLoggedIn())
    api.login(username, password)
    print(api.isLoggedIn())
    adId = api.postAd('myAd.inf')
    print(adId)
    #[api.deleteAd(ad) for ad in api.getAllAds()]
    api.logout()
    print(api.isLoggedIn())

if __name__ == "__main__":
    #api = KijijiApi()
    #pi.login(username, password)
    #api.postAd('myAd.inf')
    main()
