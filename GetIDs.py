import codecs
from bs4 import BeautifulSoup


def dictify(ul, area_id=None):
    """
    :param ul: the top UL of your HTML file
    :return: nested dictionnaries of all the cities/regions IDs
    """

    result = {}
    if area_id:
        result['area_id'] = area_id

    for li in ul.find_all("li", recursive=False):
        key = li.find('a').get('title')
        id = li.get('id').strip('group-')
        ul = li.find("ul")

        if not key.startswith("All of"):
            if ul:
                result[key] = dictify(ul, id)
            else:
                result[key] = id

    return result


def find_where(d):
    """
    :param d: a dictionnary
    :return: a tuple containing the location id and area id of the selected region
    """
    keys = sorted(d.keys())

    print()  # empty space

    # print a numbered list (starting with number 1) of all the regions
    for num, name in enumerate(keys, 1):
        if not name == "area_id":
            print(num, "-", name)

    # make sure the input is a number and a valid index
    while True:
        answer = input('\nWhere are you?')

        if answer.isdigit():
            if 0 < int(answer) <= len(keys):

                # getting the value
                value = d[keys[int(answer) - 1]]

                break

        print("Enter a valid number!")

    # if the selected value is a dictionnary, we list it again
    if isinstance(value, dict):
        return find_where(value)

    # else we return the location
    print("Here's your location ID:", value)
    print("And your location area:", d['area_id'])

    return (value, d['area_id'])


def get_location_and_area_ids():
    # a copy/paste of the dropdown list source code
    f = codecs.open('kijiji_dropdown.html', 'r', 'utf-8')

    soup = BeautifulSoup(f, 'lxml')

    # turn the top UL of the HTML file into a dictionnary
    provinces = dictify(soup.body.ul)

    return find_where(provinces)

    # from pprint import pprint
    # pprint(provinces)
    # print(provinces['Québec']['Greater Montréal']['Longueuil / South Shore'])

if __name__ == "__main__":
    get_location_and_area_ids()
