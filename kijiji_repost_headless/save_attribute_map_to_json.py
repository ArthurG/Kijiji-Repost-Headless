import bs4, requests, json
from kijiji_api import get_token
from kijiji_settings import KIJIJI_USERNAME, KIJIJI_PASSWORD

session = requests.session()

# Login to Kijiji
url = 'http://www.kijiji.ca/h-kitchener-waterloo/1700212'
resp = session.get(url)

url = 'https://www.kijiji.ca/t-login.html'
resp = session.get(url)

payload = {'emailOrNickname': KIJIJI_USERNAME,
            'password': KIJIJI_PASSWORD,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': get_token(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
resp = session.post(url, data = payload)

#Returns a list of category IDs mapped to their corresponding kijiji category name
# Example: {'214': 'apartments, condos > 2 bedroom', '782': 'computer accessories > monitors', '174': 'used cars & trucks'}
def get_category_map(session, branchCategories, is_initial_run):
    leaf_category = {}
    new_branches = {}
    if is_initial_run:
        select_category_page = session.get("https://www.kijiji.ca/p-select-category.html")
        category_soup = bs4.BeautifulSoup(select_category_page.text, "html.parser")
        for category_node in category_soup.select('[id^=CategoryId]'):
            category_name = category_node.get_text().strip("\n").strip()
            category_id = category_node['data-cat-id']
            if (category_node['data-cat-leaf']=='false'):
                new_branches[category_id] = category_name
            else:
                leaf_category[category_id] = category_name
    elif not is_initial_run and not branchCategories:
        return {}
    else:
        for [cat_id, name] in branchCategories.items():
            inner_select_url = 'https://www.kijiji.ca/p-select-category.html?categoryId='+cat_id
            select_category_page = session.get(inner_select_url)
            category_soup = bs4.BeautifulSoup(select_category_page.text, 'html.parser')
            for category_node in category_soup.select('[class=category-link]'):
                category_name = name + " > " + category_node.get_text().strip("\n").strip()
                category_id = category_node['data-cat-id']
                if (category_node['data-cat-leaf']=='false'):
                    new_branches[category_id] = category_name
                else:
                    leaf_category[category_id] = category_name
    return {**leaf_category, **(get_category_map(session, new_branches, False))}

# This is the dictionary that would need to be saved in a json file
postAdAttributes = []
"""
postAdAttributes is a list of dictionaries that should look like this:

{
"category_name": "computer accessories > monitors",
"category_id": "782",
"attributes": [
  {
    "attribute_options": [
      {
        "option_name": "18\" and under",
        "option_id": "monitorunder18inch"
      },
      {
        "option_name": "19\"-20\"",
        "option_id": "monitor19to20inch"
      },
      {
        "option_name": "21\"-24\"",
        "option_id": "monitor21to24inch"
      },
      {
        "option_name": "25\"+",
        "option_id": "monitor25inchandabove"
      }
    ],
    "attribute_id": "monitorsize_s",
    "attribute_name": "Screen Size:"
  },
  {
    "attribute_options": [
      {
        "option_name": "Owner",
        "option_id": "ownr"
      },
      {
        "option_name": "Business",
        "option_id": "delr"
      }
    ],
    "attribute_id": "forsaleby_s",
    "attribute_name": "For Sale By:"
  }
]
}
"""

for category_id, category_name in get_category_map(session, [], True).items():
    print("Searching", category_name, "...\n")


    category_props = {}
    category_props['category_id'] = category_id
    category_props['category_name'] = category_name
    category_props['attributes'] = []

    postingUrl="https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId="+category_id
    newAdPage = session.get(postingUrl)
    newAdPageSoup = bs4.BeautifulSoup(newAdPage.text, 'html.parser')

    #Find all the input boxes where the user is required to give input
    select_and_input = newAdPageSoup.find_all(['select', 'input'], {"name": lambda x: x and x.startswith('postAdForm.attributeMap')})

    for item in select_and_input:

        #Human readable name of input box
        item_label = newAdPageSoup.find('label', {'for': item['id']})

        #Current attribute being examined
        attributes = {}
        attributes['attribute_id'] = item['id']
        attributes['attribute_name'] = item_label.text.replace('\n','').strip()

        if item.name == "select":
            attributes['attribute_options'] = [{"option_id": option['value'], "option_name" : option.text} for option in item.select('option') if option['value'] != ""]

        elif item.name == "input":

            # if it's a text input, there's no options, the user must enter something manually
            if item['type'] == 'text':
                attributes['attribute_options'] = None

            else:
                item_name = item.parent.text.replace('\n', '')

                # if the attribute is already in the dictionary... add the option to the options dict
                att = next((attribute for attribute in category_props['attributes'] if attribute.get("attribute_id") == item['id']), None)
                if att:
                    att['attribute_options'].append({"option_id": item['value'], "option_name": item_name})
                    continue

                # else, create the attribute dict and the options dict
                else:
                    attributes['attribute_options'] = [{"option_id": item['value'], "option_name": item_name}]

        category_props['attributes'].append(attributes)

    postAdAttributes.append(category_props)

with open('kijiji_categories_attrs.json', 'w') as fp:
    json.dump(postAdAttributes, fp)
