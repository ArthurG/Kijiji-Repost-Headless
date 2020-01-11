import json
import requests


def find_where(d, area_id=None):
    """
    :param d: dictionary available here: http://www.kijiji.ca/j-locations.json
    :param area_id: string, parent's region's ID 
    :return: tuple, containing the location id and area id of the selected_dict region 
    """
    list_of_dicts = sorted(d['children'], key=lambda k: k['nameEn'])

    print()  # empty space

    # print a numbered list (starting with number 1) of all the regions
    for num, dictionary in enumerate(list_of_dicts, 1):
        print(num, "-", dictionary['nameEn'])

    # make sure the input is a number and a valid index
    while True:
        index = input('\nWhere are you? ')
        if index.isdigit():
            if 0 < int(index) <= len(list_of_dicts):
                selected_dict = list_of_dicts[int(index) - 1]
                break
        print("Enter a valid number!")

    # if the selected dictionary has children, we list it again
    if len(selected_dict['children']) > 0:
        return find_where(selected_dict, selected_dict['id'])

    # else we return the location
    print("Here's your location ID:", selected_dict['id'])
    print("And your location area:", area_id)

    return selected_dict['id'], area_id


def get_location_and_area_ids():
    locations_url = 'http://www.kijiji.ca/j-locations.json'
    locations_page = requests.get(locations_url)
    # get rid of javascript variable name and trailing semi-colon
    locations_data = locations_page.text.split(" = ")[1].strip()[:-1]
    locations_dict = json.loads(locations_data)

    return find_where(locations_dict)


if __name__ == "__main__":
    get_location_and_area_ids()
