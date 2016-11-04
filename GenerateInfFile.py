#TODO: Actual error handling

import requests
import json
from PostingCategory import *
adType = ['OFFER', 'WANTED']
priceType = ['FIXED','GIVE_AWAY', 'CONTACT', 'SWAP_TRADE']



#Dictionary w/ postal_code, lat, lng, city, province
def getAddressMap():
    address = input("What is your address?")
    data={'address': address}
    endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
    resp = requests.get(endpoint,params=data)

    ans = {}
    latlng = json.loads(resp.text)['results'][0]['geometry']['location']

    ans['lat'] = str(latlng['lat'])
    ans['lng'] = str(latlng['lng'])
    postalCode = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "postal_code" in item['types'] ][0]['short_name']
    city = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "locality" in item['types'] ][0]['short_name']
    province = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "administrative_area_level_1" in item['types'] ][0]['short_name']
    ans['postal_code'] = postalCode
    ans['city'] = city
    ans['province'] = province
    return ans

def getEnum(array):
    print("Which of the following pertains most to you?")
    for i, item in enumerate(array):
        print(i+1, ".", item)
    response = int(input())
    return array[response-1]

#{'category': catId, 'attirbute: 'attrid', 'attribute': 'attrid''}}
def pickCategory():
    ans = {}
    keyword = input("Please give a keyword for your category")
    possibleCategories = sqliteSession.query(PostingCategory).filter(PostingCategory.name.like("%"+keyword+"%"))
    for i, cat in enumerate(possibleCategories):
        print(i+1, ". ", cat)
    print("Which category is most related?")
    response = int(input())
    selectedCategory = possibleCategories[response-1]
    ans['category'] = selectedCategory.kijijiId
    for attribute in selectedCategory.attribute:
        for i, attrValue in enumerate(attribute.acceptableValue):
            print(i+1, attrValue.value)
        response = int(input("Which one is most relevant relating to " + attribute.kijijiName + "?"))
        ans[attribute.kijijiName] = attribute.acceptableValue[response-1].kijijiValue
    return ans

categoryMap = pickCategory()
addressMap = getAddressMap()
title = input("What's the title of your item?")
description = input("What's the description of your item?")
pmtType = getEnum(priceType)
if pmtType == 'FIXED':
    price = input("How much are you selling for?")
ad = getEnum(adType)
photos = input("Give me the names of your photos, separated by a comma")

f = open('myAd.inf', 'w')
f.write("postAdForm.geocodeLat="+addressMap['lat']+"\n")
f.write("postAdForm.geocodeLng="+addressMap['lng']+"\n")
f.write("postAdForm.city="+addressMap['city']+"\n")
f.write("postAdForm.province="+addressMap['province']+"\n")
f.write("PostalLat="+addressMap['lat']+"\n")
f.write("PostalLng="+addressMap['lng']+"\n")
f.write("categoryId="+categoryMap['category']+"\n")
f.write("postAdForm.adType="+ad+"\n")
f.write("postAdForm.priceType="+pmtType+"\n")
if pmtType == 'FIXED':
    f.write("postAdForm.priceAmount="+price+"\n")
[f.write("postAdForm.attributeMap["+attrKey+"]="+attrVal+"\n") for attrKey, attrVal in categoryMap.items() if attrKey != "category"]
f.write("postAdForm.attributeMap[forsaleby_s]=ownr"+"\n")
f.write("postAdForm.title="+title+"\n")
f.write("postAdForm.description="+description+"\n")
f.write("postAdForm.locationId=1700212"+"\n") #TODO: Get this info from user
f.write("locationLevel0=1700209"+"\n")
f.write("postAdForm.postalCode="+addressMap['postal_code']+"\n")
f.write("featuresForm.topAdDuration=7"+"\n")
f.write("submitType=saveAndCheckout"+"\n")
f.write("imageCsv="+photos+"\n")
f.close()
