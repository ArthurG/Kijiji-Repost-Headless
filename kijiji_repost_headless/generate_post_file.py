# TODO: Actual error handling

import json
from operator import itemgetter
import os
import yaml

import requests

from get_ids import get_location_and_area_ids


adType = ['OFFER', 'WANTED']
priceType = ['FIXED', 'GIVE_AWAY', 'CONTACT', 'SWAP_TRADE']


# Dictionary w/ postal_code, lat, lng, city, province
def get_address_map():
    address = input("Your address: ")
    data = {'address': address}
    endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
    resp = requests.get(endpoint, params=data)

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


def get_enum(array):
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


# {'category': catId, 'attirbute: 'attrid', 'attribute': 'attrid''}}
def pick_category():
    ans = {}

    filename = os.path.join(os.path.dirname(__file__), 'kijiji_categories_attrs.json')
    kijiji_categories_and_attributes = json.load(open(filename, 'r'))

    while True:
        keyword = input("Please provide a category keyword to search for: ")
        possible_categories = [cat for cat in kijiji_categories_and_attributes if keyword.lower() in cat['category_name'].lower()]
        if len(possible_categories) < 1:
            print("Could not find any categories using the given keyword. Try again.")
        else:
            break

    for i, cat in enumerate(sorted(possible_categories, key=itemgetter('category_name'))):
        print("{:>2d} - {}".format(i + 1, cat['category_name']))

    # make sure the input is a number and a valid index
    while True:
        response = input("Select a category from the list above (choose number) [To restart, enter 0]: ")
        if response == "0":
            print()  # empty line
            return None  # this will restart pick_category
        if response.isdigit():
            if 0 < int(response) <= len(possible_categories):
                selectedCategory = sorted(possible_categories, key=itemgetter('category_name'))[int(response) - 1]
                break
        print("Enter a valid number!")

    ans['category'] = selectedCategory['category_id']

    for attribute in selectedCategory['attributes']:
        if (attribute['attribute_options'] == None):
            ans[attribute['attribute_id']] = input("Enter a value related to {}: ".format(attribute['attribute_name']))
        else:
            for i, attrValue in enumerate(attribute['attribute_options']):
                print(i + 1, attrValue['option_name'])

            # make sure the input is a number and a valid index
            while True:
                response = input("Choose most relevant category relating to " + attribute[
                    'attribute_name'] + " [To restart, enter 0] : ")
                if response == "0":
                    print()  # empty line
                    return None  # this will restart pick_category
                if response.isdigit():
                    if 0 < int(response) <= len(attribute['attribute_options']):
                        ans[attribute['attribute_id']] = attribute['attribute_options'][int(response) - 1]['option_id']
                        break
                print("Enter a valid number!")

    return ans


# Multiline ad description
def get_description():
    contents = []
    print("Enter multiline ad description.")
    print("Type 'DEL' on a new line to delete last line. Type 'EOF' on a new line to finish.")
    while True:
        line = input()
        if line.upper() == "EOF":
            break
        elif line.upper() == "DEL":
            if contents:
                print('"{}" was deleted. Enter next line.'.format(contents.pop()))
            else:
                print("This is the last line.")
            continue
        contents.append(line)
    return "\\n".join(contents)


def run_program():
    print("*****************************************************************")
    print("* Creating the item.yaml file. Please answer all the questions. *")
    print("*****************************************************************\n")

    print("Your ad must be submitted in a specific category.")

    categoryMap = restart_function(pick_category)
    addressMap = get_address_map()
    locationId, locationArea = get_location_and_area_ids()  # returns a tuple containing the location ID and area ID
    title = input("Ad title: ")
    description = get_description()
    print("Ad price type:")
    pmtType = get_enum(priceType)
    if pmtType == 'FIXED':
        price = input("Ad price in dollars: ")
    print("Ad type:")
    ad = get_enum(adType)
    photos = []
    photos_len = int(input("Specify how many images are there to upload: "))
    for i in range(photos_len):
        photos.append(input("Specify the path of image #{} relative to the .yaml file: ".format(i+1)))

    username = input("Kijiji username: ")
    password = input("Kijiji password: ")

    details = {}

    details['postAdForm.geocodeLat'] = addressMap['lat']
    details['postAdForm.geocodeLng'] = addressMap['lng']
    details['PostalLat'] = addressMap['lat']
    details['PostalLng'] = addressMap['lng']
    details['postAdForm.city'] = addressMap['city']
    details['postAdForm.addressCity'] = addressMap['city']
    details['postAdForm.province'] = addressMap['province']
    details['postAdForm.addressProvince'] = addressMap['province']
    details['postAdForm.postalCode'] = addressMap['postal_code']
    details['postAdForm.addressPostalCode'] = addressMap['postal_code']
    details['categoryId'] = categoryMap['category']
    details['postAdForm.adType'] = ad
    details['postAdForm.priceType'] = pmtType
    if pmtType == 'FIXED':
        details["postAdForm.priceAmount"] = price
    for attrKey, attrVal in categoryMap.items():
        if attrKey != "category":
            details["postAdForm.attributeMap[{}]".format(attrKey)] = attrVal

    details["postAdForm.title"]=title
    details["postAdForm.description"]=description
    details["postAdForm.locationId"]=locationId
    details["locationLevel0"]=locationArea
    details["topAdDuration"]="7"
    details["submitType"]="saveAndCheckout"
    details["image_paths"]=photos

    details["username"]=username
    details["password"]=password

    f = open("item.yaml", "w")
    f.write(yaml.dump(details))
    f.close()

    print("\"item.yaml\" file created. Use this file to post your ad.")


if __name__ == '__main__':
    run_program()
