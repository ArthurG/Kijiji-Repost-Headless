#TODO: Actual error handling

import requests
import json
from PostingCategory import *
adType = ['OFFER', 'WANTED']
priceType = ['FIXED', 'GIVE_AWAY', 'CONTACT', 'SWAP_TRADE']


#Dictionary w/ postal_code, lat, lng, city, province
def getAddressMap():
    address = input("Your address: ")
    data = {'address': address}
    endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
    resp = requests.get(endpoint,params=data)

    ans = {}
    latlng = json.loads(resp.text)['results'][0]['geometry']['location']
    ans['lat'] = str(latlng['lat'])
    ans['lng'] = str(latlng['lng'])
    postalCode = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "postal_code" in item['types'] ][0]['short_name']
    city = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "administrative_area_level_3" in item['types'] or "locality" in item['types'] ][0]['short_name']
    province = [item for item in json.loads(resp.text)['results'][0]['address_components'] if "administrative_area_level_1" in item['types'] ][0]['short_name']
    ans['postal_code'] = postalCode
    ans['city'] = city
    ans['province'] = province
    return ans

def getEnum(array):
    for i, item in enumerate(array):
        print("{:>2d} - {}".format(i+1, item))
    response = int(input("Choose one: "))
    return array[response-1]

#{'category': catId, 'attirbute: 'attrid', 'attribute': 'attrid''}}
def pickCategory():
    ans = {}
    while True:
        keyword = input("Provide a category keyword to search for: ")
        possibleCategories = sqliteSession.query(PostingCategory).filter(PostingCategory.name.like("%"+keyword+"%"))
        if possibleCategories.count() < 1:
            print("Could not find any categories using the given keyword. Try again.")
        else:
            break
    for i, cat in enumerate(possibleCategories):
        print("{:>2d} - {}".format(i+1, cat))
    response = int(input("Select a category from the list above (choose number): "))
    selectedCategory = possibleCategories[response-1]
    ans['category'] = selectedCategory.kijijiId
    for attribute in selectedCategory.attribute:
        for i, attrValue in enumerate(attribute.acceptableValue):
            print(i+1, attrValue.value)
        response = int(input("Choose most relevant category relating to " + attribute.kijijiName + ": "))
        ans[attribute.kijijiName] = attribute.acceptableValue[response-1].kijijiValue
    return ans

# Multiline ad description
def getDescription():
    contents = []
    print("Enter multiline ad description. Type 'EOF' on a new line to finish.")
    while True:
        line = input()
        if line == "EOF":
            break
        contents.append(line)
    return "\\n".join(contents)


categoryMap = pickCategory()
addressMap = getAddressMap()
# TODO: Figure out a way to determine appropriate location ID and location area ID from geolocation coords
locationId = "1700212"
locationArea = "1700209"
title = input("Ad title: ")
description = getDescription()
print("Ad price type:")
pmtType = getEnum(priceType)
if pmtType == 'FIXED':
    price = input("Ad price in dollars: ")
print("Ad type:")
ad = getEnum(adType)
photos = input("List of image filenames to upload (comma separated): ")

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
f.write("postAdForm.locationId="+locationId+"\n")
f.write("locationLevel0="+locationArea+"\n")
f.write("postAdForm.postalCode="+addressMap['postal_code']+"\n")
f.write("featuresForm.topAdDuration=7"+"\n")
f.write("submitType=saveAndCheckout"+"\n")
f.write("imageCsv="+photos+"\n")
f.close()
