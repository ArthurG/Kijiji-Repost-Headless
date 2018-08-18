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

for category_id in range(0,1000):
    print("Searching category_id {}".format(category_id))

    category_props = {}
    category_props['category_id'] = category_id

    category_props['attributes'] = []

    postingUrl="https://www.kijiji.ca/p-post-ad.html?categoryId={}".format(category_id)
    newAdPage = session.get(postingUrl)
    newAdPageSoup = bs4.BeautifulSoup(newAdPage.text, 'html.parser')

    #Find whether the category is actually valid
    title_input_div = newAdPageSoup.find_all(['textarea'], {"id": "AdTitleForm"})

    #Find the category name
    category_name = newAdPageSoup.select("div.form-section strong")
    if len(category_name) == 0:
        continue

    category_props['category_name'] = ">".join([name.get_text().strip("\n").strip() for name in category_name])

    #Find all the input boxes where the user is required to give input
    select_boxes = newAdPageSoup.find_all(['select'], {"name": lambda x: x and x.startswith('postAdForm')})
    input_boxes = newAdPageSoup.find_all(['input'], {"name": lambda x: x and x.startswith('postAdForm'), "type": "text"})
    input_radios = newAdPageSoup.find_all(['input'], {"name": lambda x: x and x.startswith('postAdForm'), "type": "radio"})

    useless_attributes_array = ["pstad-email"]
    for item in select_boxes:
        attributes = {}

        #Human readable name of input box
        item_label = newAdPageSoup.find('label', {'for': item['id']})
        if item_label is None:
           # This branch will be used for real estate categoories ie: categoryId=35
           item_label = item.parent.findNext("p")

        #Current attribute being examined
        attributes['attribute_id'] = item['id']
        attributes['attribute_name'] = item_label.text.replace('\n','').strip()

        attributes['attribute_options'] = [{"option_id": option['value'], "option_name" : option.text} for option in item.select('option') if option['value'] != ""]
        category_props['attributes'].append(attributes)

    for item in input_boxes:
        attributes = {}
        item_label = newAdPageSoup.find('label', {'for': item['id']})
        if item['id'] in useless_attributes_array:
            continue

        #Current attribute being examined
        attributes['attribute_id'] = item['id']

        attributes['attribute_options'] = None

        category_props['attributes'].append(attributes)

    for item in input_radios:
        attributes = {}
        item_label = newAdPageSoup.find('label', {'for': item['id']})

        attributes = {}
        attributes['attribute_id'] = item['id']
        attributes['attribute_name'] = item_label.text.replace('\n','').strip()

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
