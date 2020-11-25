# TODO: Actual error handling

import json
import os
from collections import OrderedDict
from operator import itemgetter

import requests
from random import choice
import yaml

from get_ids import get_location_and_area_ids

user_agents = [
    # Random list of top UAs for mac and windows/ chrome & FF
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/74.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/74.0"
]
session_ua = choice(user_agents) # Randomly selects a UA from the list.
request_headers = {"User-Agent": session_ua}

ad_file_name = 'item.yaml'
ad_type = ['OFFER', 'WANTED']
price_type = ['FIXED', 'GIVE_AWAY', 'CONTACT', 'SWAP_TRADE']


def represent_ordereddict(dumper, data):
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        value.append((node_key, node_value))
    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


yaml.add_representer(OrderedDict, represent_ordereddict)


# Dictionary w/ postal_code, lat, lng, city, province
def get_address_map():
    address = input("Your address: ")
    resp = requests.get(
        'https://nominatim.openstreetmap.org/search', 
        params={'q': address, 'addressdetails': 1, 'format':'json'},
        headers=request_headers
    )
    resp.raise_for_status()

    results = json.loads(resp.text)
    if len(results) == 0:
        print("Found no results! Try again.")
        print()  # Empty line
        return None  # Restart

    if len(results) > 1:
        # Multiple results, prompt for choice
        for i, result in enumerate(sorted(results, key=itemgetter('display_name'))):
            print("{:>2d} - {}".format(i + 1, result['display_name']))

        while True:
            response = input("Select a result from the list above (choose number) [To restart, enter 0]: ")
            if response == "0":
                print()  # Empty line
                return None  # Restart
            if response.isdigit():
                if 0 < int(response) <= len(results):
                    chosen_result = sorted(results, key=itemgetter('display_name'))[int(response) - 1]
                    break
            print("Enter a valid number!")
    else:
        # Must only be one result, don't prompt for choice
        # No results case was already handled above by checking 'status' field of Google maps API response
        chosen_result = results[0]
        print("Found one result: {}".format(chosen_result['display_name']))

    try:
        postal_code = chosen_result['address']['postcode'] 
    except (IndexError, KeyError):
        print("Address is too vague; postal code is missing! Try again...")
        print()  # Empty line
        return None  # Restart

    if "city" in chosen_result['address']:
        city = chosen_result['address']['city'] 
    elif "town" in chosen_result['address']:
        city = chosen_result['address']['town'] 
    else:
        print("Address is too vague; city is missing! Try again.")
        print()  # Empty line
        return None  # Restart

    try:
        province = chosen_result['address']['state'] 
    except (IndexError, KeyError):
        print("Address is too vague; province is missing! Try again.")
        print()  # Empty line
        return None  # Restart

    ans = {}
    ans['lat'] = str(chosen_result['lat'])
    ans['lng'] = str(chosen_result['lon'])
    ans['postal_code'] = postal_code
    ans['city'] = city
    ans['province'] = province

    return ans


def get_enum(array):
    for i, item in enumerate(array):
        print("{:>2d} - {}".format(i+1, item))
    response = int(input("Choose one: "))
    return array[response - 1]


def restart_function(func):
    """
    :param func: a function that returns None if it needs to be rerun 
    :return: the value returned by func
    """
    while True:
        returned_value = func()
        if returned_value is None:
            continue
        else:
            break
    return returned_value


# {'category': catId, 'attirbute: 'attrid', 'attribute': 'attrid''}}
def pick_category():
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

    # Make sure the input is a number and a valid index
    while True:
        response = input("Select a category from the list above (choose number) [To restart, enter 0]: ")
        if response == "0":
            print()  # Empty line
            return None  # Restart
        if response.isdigit():
            if 0 < int(response) <= len(possible_categories):
                selected_category = sorted(possible_categories, key=itemgetter('category_name'))[int(response) - 1]
                break
        print("Enter a valid number!")

    ans = {}
    ans['category'] = selected_category['category_id']

    for attribute in selected_category['attributes']:
        if attribute['attribute_type'] == "input":
            ans[attribute['attribute_name']] = input("Enter a value related to \"{}\": ".format(attribute['attribute_human_readable']))
        else:
            for i, attr_value in enumerate(attribute['attribute_options']):
                print(i + 1, attr_value['option_human_readable'])

            # Make sure the input is a number and a valid index
            while True:
                response = input("Choose most relevant category relating to \"{}\". [To skip, enter 'skip'] [To restart, enter 0]: ".format(attribute['attribute_human_readable']))
                if response == "skip":
                    break
                if response == "0":
                    print()  # Empty line
                    return None  # Restart
                if response.isdigit():
                    if 0 < int(response) <= len(attribute['attribute_options']):
                        ans[attribute['attribute_name']] = attribute['attribute_options'][int(response) - 1]['option_name']
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
    print("****************************************************************")
    print("* Creating the item.yaml file. Please answer all the questions. *")
    print("****************************************************************\n")

    print("Your ad must be submitted in a specific category.")

    category_map = restart_function(pick_category)
    address_map = restart_function(get_address_map)
    location_id, location_area = get_location_and_area_ids()  # Returns a tuple containing location ID and area ID
    description = get_description()
    print("Ad type:")
    photos = []
    photos_len = int(input("Specify how many images are there to upload: "))
    for i in range(photos_len):
        photos.append(input("Specify the path of image #{} relative to the .yaml file: ".format(i+1)))

    details = OrderedDict()
    for attrKey, attrVal in category_map.items():
        if attrKey != 'category':
            details[attrKey] = attrVal
    details['postAdForm.city'] = address_map['city']
    details['postAdForm.province'] = address_map['province']
    details['postAdForm.postalCode'] = address_map['postal_code']
    details['postAdForm.addressCity'] = address_map['city']
    details['postAdForm.addressProvince'] = address_map['province']
    details['postAdForm.addressPostalCode'] = address_map['postal_code']
    details['postAdForm.geocodeLat'] = address_map['lat']
    details['postAdForm.geocodeLng'] = address_map['lng']
    details['postAdForm.locationId'] = location_id
    details['PostalLat'] = address_map['lat']
    details['PostalLng'] = address_map['lng']
    details['locationLevel0'] = location_area
    details['topAdDuration'] = "7"
    details['submitType'] = "saveAndCheckout"
    details['postAdForm.description'] = description
    details['categoryId'] = category_map['category']
    details['image_paths'] = photos

    f = open(ad_file_name, 'w')
    f.write(yaml.dump(details))
    f.close()

    print("\"{}\" file created. Use this file to post your ad.".format(ad_file_name))


if __name__ == "__main__":
    run_program()
