import sqlalchemy
import bs4
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, sessionmaker
import sqlalchemy.ext.declarative

engine = sqlalchemy.create_engine('sqlite:///kijiji_api.db')
Base = sqlalchemy.ext.declarative.declarative_base()

class PostingCategory(Base):
    __tablename__ = "postingCategory"
    _id=Column(Integer(), primary_key=True)
    kijijiId=Column(String())
    name=Column(String())

    def __repr__(self):
        return "<PostingCategory(name='%s')>" % self.name

class ItemAttribute(Base):
    __tablename__ = "itemAttribute"
    _id=Column(Integer(), primary_key=True)
    kijijiName=Column(String())
    name=Column(String())
    related_categoryId = Column(Integer(), sqlalchemy.ForeignKey('postingCategory._id'))
    relatedCategory = relationship("PostingCategory", back_populates="attribute")
    def __repr__(self):
        return "<ItemAttribute(name='%s') >" % self.name

PostingCategory.attribute = relationship("ItemAttribute", back_populates="relatedCategory")

class ItemAttributeValue(Base):
    __tablename__ = "itemAttributeValue"
    _id=Column(Integer, primary_key=True)
    kijijiValue=Column(String)
    value=Column(String())
    related_attributeId=Column(Integer(), sqlalchemy.ForeignKey('itemAttribute._id'))
    attributeFor = relationship('ItemAttribute', back_populates="acceptableValue")
ItemAttribute.acceptableValue = relationship("ItemAttributeValue", back_populates="attributeFor")

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


