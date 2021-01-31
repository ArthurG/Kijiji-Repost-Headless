from iterfzf import iterfzf
import json
import requests

denormalized_locations = {}
def denormalize_location(list_of_dicts, prefix, region):
    for item in list_of_dicts:
        if 'nameEn' in item.keys() and item['nameEn']:
            new_prefix =  prefix + " > " + item['nameEn']
        elif 'regionLabel' in item.keys() and item['regionLabel']:
            new_prefix =  prefix + " > " + item['regionLabel']
        if 'children' in item.keys() and item['children']:
            denormalize_location(item['children'], new_prefix, item['id'])
        else:
            print(new_prefix)
            denormalized_locations[new_prefix] = (item['id'], region,)


def find_where(d, area_id=None):
    """
    :param d: dictionary available here: http://www.kijiji.ca/j-locations.json
    :param area_id: string, parent's region's ID 
    :return: tuple, containing the location id and area id of the selected_dict region 
    """
    list_of_dicts = sorted(d['children'], key=lambda k: k['nameEn'])
    denormalize_location(list_of_dicts, '', None)
    selected_location = iterfzf(denormalized_locations.keys())

    # else we return the location
    print("Here's your location ID:", denormalized_locations[selected_location][0])
    print("And your location area:", denormalized_locations[selected_location][1])

    return denormalized_locations[selected_location]


def get_location_and_area_ids():
    locations_url = 'http://www.kijiji.ca/j-locations.json'
    locations_page = requests.get(locations_url)
    # get rid of javascript variable name and trailing semi-colon
    locations_data = locations_page.text.split(" = ")[1].strip()[:-1]
    locations_dict = json.loads(locations_data)

    return find_where(locations_dict)


if __name__ == "__main__":
    get_location_and_area_ids()
