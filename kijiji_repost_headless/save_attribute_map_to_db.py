import bs4
import requests
import sqlalchemy.ext.declarative
from kijiji_api import get_token
from posting_category import *
from sqlalchemy.orm import sessionmaker

engine = sqlalchemy.create_engine('sqlite:///kijiji_api.db')
Base = sqlalchemy.ext.declarative.declarative_base()

def get_category_map(session, branchCategories, isInitialRun):
    leafCategory = {}
    newBranches = {}
    if isInitialRun:
        selectCategoryPage = session.get("https://www.kijiji.ca/p-select-category.html")
        categorySoup = bs4.BeautifulSoup(selectCategoryPage.text, "html.parser")
        for categoryNode in categorySoup.select('[id^=CategoryId]'):
            categoryName = categoryNode.get_text().strip("\n").strip()
            categoryId = categoryNode['data-cat-id'] 
            if (categoryNode['data-cat-leaf']=='false'):
                newBranches[categoryId] = categoryName
            else:
                leafCategory[categoryId] = categoryName
    elif not isInitialRun and not branchCategories:
        print(branchCategories)
        return {}
    else:
        for [catId, name] in branchCategories.items():
            innerSelectUrl = 'https://www.kijiji.ca/p-select-category.html?categoryId='+catId
            selectCategoryPage = session.get(innerSelectUrl)
            categorySoup = bs4.BeautifulSoup(selectCategoryPage.text, 'html.parser')
            for categoryNode in categorySoup.select('[class=category-link]'):
                categoryName = name + " > " + categoryNode.get_text().strip("\n").strip()
                categoryId = categoryNode['data-cat-id'] 
                if (categoryNode['data-cat-leaf']=='false'):
                    newBranches[categoryId] = categoryName
                else:
                    leafCategory[categoryId] = categoryName
    return {**leafCategory, **(get_category_map(session, newBranches, False))}

##INITIALIZE THE SQLALCHEMY 
Session = sessionmaker(bind=engine)
sqliteSession = Session()
Base.metadata.create_all(engine)

#Sample of how to insert values into database
"""
itemValue1=ItemAttributeValue(value="purplpe")
itemValue2=ItemAttributeValue(value="red")
itemAttr1=ItemAttribute(name="fur color")
itemAttr1.acceptableValue.append(itemValue1)
itemAttr1.acceptableValue.append(itemValue2)
category1=PostingCategory(kijijiId="123213", name="cats")
category1.attribute.append(itemAttr1)
session.add(category1)
session.commit()
"""

#Sample of how to retrive values from database
"""
for category in session.query(PostingCategory):
    print("--%s --"%category.name)
    for attribute in category.attribute:
        print("has attribute %s" %attribute.name)
        for value in attribute.acceptableValue:
            print(value.value)
"""


##Get all the categories from Kijiji and put them into database
session = requests.session()
#Login to Kijiji
url = 'http://www.kijiji.ca/h-kitchener-waterloo/1700212'
resp = session.get(url)

url = 'https://www.kijiji.ca/t-login.html'
resp = session.get(url)

payload = {'emailOrNickname': username,
            'password': password,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': get_token(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
resp = session.post(url, data = payload)

#Look at what attributes are there
categories = get_category_map(session, [], True)
for key, value in categories.items():
    print("Currently saving ", value)
    category1=PostingCategory(kijijiId=key, name=value)
    postingUrl="https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId="+key
    newAdPage = session.get(postingUrl)
    newAdPageSoup = bs4.BeautifulSoup(newAdPage.text, 'html.parser')
    attributes = newAdPageSoup.select("select[name^=postAdForm.attributeMap]")
    for attribute in attributes:
        attribute1 = ItemAttribute(name="", kijijiName= attribute["id"])
        for possibleValue in attribute.select("option"):
            if possibleValue["value"] == "":
                continue
            value1 = ItemAttributeValue(value=possibleValue.get_text(),kijijiValue=possibleValue["value"])
            attribute1.acceptableValue.append(value1)
        category1.attribute.append(attribute1)

    sqliteSession.add(category1)
sqliteSession.commit()
