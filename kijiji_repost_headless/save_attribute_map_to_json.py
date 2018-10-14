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
   'attributes':[
      {
         'attribute_human_readable':'Price:',
         'attribute_type':'input',
         'attribute_name':'postAdForm.priceAmount'
      },
      {
         'attribute_human_readable':'Ad Title:',
         'attribute_type':'input',
         'attribute_name':'postAdForm.title'
      },
      {
         'attribute_human_readable':'YouTube Video:(optional)',
         'attribute_type':'input',
         'attribute_name':'postAdForm.youtubeVideoURL'
      },
      {
         'attribute_human_readable':'PhoneNumber',
         'attribute_type':'input',
         'attribute_name':'postAdForm.phoneNumber'
      },
      {
         'attribute_options':[
            {
               'option_name':'OFFER',
               'option_human_readable':'I am offering - You are offering an item for sale'
            },
            {
               'option_name':'WANTED',
               'option_human_readable':'I want - You want to buy an item'
            }
         ],
         'attribute_human_readable':'',
         'attribute_type':'radio',
         'attribute_name':'postAdForm.adType'
      },
      {
         'attribute_options':[
            {
               'option_name':'FIXED',
               'option_human_readable':'$'
            },
            {
               'option_human_readable':'Free'
            },
            {
               'option_name':'CONTACT',
               'option_human_readable':'Please Contact'
            },
            {
               'option_name':'SWAP_TRADE',
               'option_human_readable':'Swap / Trade'
            }
         ],
         'attribute_human_readable':'',
         'attribute_type':'radio',
         'attribute_name':'postAdForm.priceType'
      }
   ],
   'category_id':5,
   'category_name':'Community>Rideshare'
}
"""

all_categories = set()
# Perform a depth first search for finding list of categories on Kijiji
def find_categories(category_id):
    select_cat_url = "https://www.kijiji.ca/j-select-category.json"
    resp = requests.get(select_cat_url, params={'categoryId': category_id, 't': 1539032850451})
    results = json.loads(resp.text)
    for level in results:
        for item in results[level].get('items', []):
            categoryId = item['categoryId']
            if categoryId not in all_categories:
                all_categories.add(categoryId)
                find_categories(categoryId)
find_categories(10)

# Save the attributes of each category
for category_id in all_categories:
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
        #Human readable label of select box
        item_label = newAdPageSoup.find('label', {'for': item['id']})

        if item_label is None:
           # This branch will be used for real estate categoories ie: categoryId=35
           item_label = item.parent.findNext("p")

        #Current attribute being examined
        attributes = {}
        attributes['attribute_type'] = "select"
        attributes['attribute_name'] = item['name']
        attributes['attribute_human_readable'] = item_label.text.replace('\n','').strip()

        attributes['attribute_options'] = [{"option_name": option['value'], "option_human_readable" : option.text.strip().lstrip()} for option in item.select('option') if option['value'] != ""]
        category_props['attributes'].append(attributes)

    for item in input_boxes:
        #Human readable label of input box
        item_label = newAdPageSoup.find('label', {'for': item['id']})

        #Current attribute being examined
        attributes = {}
        attributes['attribute_type'] = "input"
        attributes['attribute_name'] = item['name']
        if item_label is None:
            attributes['attribute_human_readable'] = item["id"]
        else:
            attributes['attribute_human_readable'] = item_label.text.replace('\n','').strip()

        if item['id'] in useless_attributes_array:
            continue

        category_props['attributes'].append(attributes)

    for item in input_radios:
        #Human readable label of radio
        item_label = newAdPageSoup.find('label', {'for': item['id']})

        #Current attribute being examined
        attributes = {}
        attributes['attribute_type'] = "radio"
        attributes['attribute_name'] = item['name']
        attributes['attribute_human_readable'] = item_label.text.replace('\n','').strip()

        item_name = item.parent.text.replace('\n', '').strip().lstrip()

        # if the attribute is already in the dictionary... add the option to the options dict
        att = next((attribute for attribute in category_props['attributes'] if attribute.get("attribute_name") == item['name']), None)
        if att:
            att['attribute_options'].append({"option_name": item['value'], "option_human_readable": item_name})
            continue
        # else, create the attribute dict and the options dict
        else:
            attributes['attribute_options'] = [{"option_name": item['value'], "option_human_readable": item_name}]
        category_props['attributes'].append(attributes)

    postAdAttributes.append(category_props)

with open('kijiji_categories_attrs.json', 'w') as fp:
    json.dump(postAdAttributes, fp)
