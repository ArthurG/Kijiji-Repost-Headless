#TODO: Actual error handling

import requests
import json
from PostingCategory import *
from GetIDs import get_location_and_area_ids
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

def restart_function(func):
    """
    :param func: a function that returns None if it needs to be rerun 
    :return: the value returned by func
    """
    while True:
        returned_value = func()
        if returned_value == None:
            continue
        else:
            break
    return returned_value

#{'category': catId, 'attirbute: 'attrid', 'attribute': 'attrid''}}
def pickCategory():
    ans = {}
    while True:
        keyword = input("Please provide a category keyword to search for: ")
        possibleCategories = sqliteSession.query(PostingCategory).filter(PostingCategory.name.like("%"+keyword+"%"))
        if possibleCategories.count() < 1:
            print("Could not find any categories using the given keyword. Try again.")
        else:
            break
    for i, cat in enumerate(possibleCategories):
        print("{:>2d} - {}".format(i+1, cat))

    # make sure the input is a number and a valid index
    while True:
        response = input("Select a category from the list above (choose number) [To restart, enter 0]: ")
        if response == "0":
            print()  # empty line
            return None  # this will restart pickCategory
        if response.isdigit():
            if 0 < int(response) <= possibleCategories.count():
                selectedCategory = possibleCategories[int(response) - 1]
                break
        print("Enter a valid number!")

    ans['category'] = selectedCategory.kijijiId
    for attribute in selectedCategory.attribute:
        for i, attrValue in enumerate(attribute.acceptableValue):
            print(i+1, attrValue.value)

        # make sure the input is a number and a valid index
        while True:
            response = input("Choose most relevant category relating to " + attribute.kijijiName + " [To restart, enter 0] : ")
            if response == "0":
                print()  # empty line
                return None  # this will restart pickCategory
            if response.isdigit():
                if 0 < int(response) <= len(attribute.acceptableValue):
                    ans[attribute.kijijiName] = attribute.acceptableValue[int(response) - 1].kijijiValue
                    break
            print("Enter a valid number!")

    return ans

# Multiline ad description
def getDescription():
    contents = []
    print("Enter multiline ad description.")
    print("Type 'DEL' on a new line to delete last line. Type 'EOF' on a new line to finish.")
    while True:
        line = input()
        if line.upper() == "EOF":
            break
        elif line.upper() == "DEL":
            if contents:
                print('"' + contents.pop() + '" was deleted. Enter next line.')
            else:
                print("This is the last line.")
            continue
        contents.append(line)
    return "\\n".join(contents)


if __name__ == '__main__':
    print("****************************************************************")
    print("* Creating the myAd.inf file. Please answer all the questions. *")
    print("****************************************************************\n")

    print("Your ad must be submitted in a specific category.")

    categoryMap = restart_function(pickCategory)
    addressMap = getAddressMap()
    locationId, locationArea = get_location_and_area_ids()  # returns a tuple containing the location ID and area ID
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

    print("myAd.inf file created. Use this file to post your ad.")
