# doing necessary imports
import logging
from datetime import datetime
from flask import Flask, render_template, request,jsonify
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq, Request
import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO, filename='logfile.txt', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)
today_date = datetime.today().strftime('%Y-%m-%d')
# Specify your browser's user agent string
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"

app = Flask(__name__)  # initialising the flask app with the name 'app'


@app.route('/', methods =['POST','GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ","") # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            db = dbConn['crawlerDB']             # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            reviews_list = list(reviews)
            if len(reviews_list) > 0:  # if there are documents in the collection
                return render_template('results.html', reviews=reviews_list)
            else:
                page_url = "https://www.jumia.com.ng/catalog/?q=" + searchString # preparing the URL to search the product on  Jumia
                # Specify your browser's user agent string
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
                # Create a Request object with the URL and headers
                url_page = requests.get(page_url, headers={'User-Agent': user_agent})
                page_html = bs(url_page.content, "html.parser") # parsing the webpage as HTML
                bigboxes = page_html.findAll("article", {"class": "prd _fb col c-prd"}) # seacrhing for appropriate tag to redirect to the product link
                #del bigboxes[0:3] # the first 3 members of the list do not contain relevant information, hence deleting them.
                #box = bigboxes[0] #  taking the first iteration (for demo)
                for box in bigboxes:
                    productLink= "https://www.jumia.com.ng" + box.findAll('a')[1]['href']
                    prodRes = requests.get(productLink, headers={'User-Agent': user_agent})  # getting the product page from serve
                    prod_html = bs(prodRes.text, features="html.parser")  # parsing the product page as HTML
                    reveiw_section = prod_html.find_all("section", {"class": "card aim -mtm"})
                    try:
                        productAllReviewLink = "https://www.jumia.com.ng" + reveiw_section[0].find('a')['href']
                        #print(productAllReviewLink )
                    except:
                        pass

                    revRes = requests.get(productAllReviewLink , headers={'User-Agent': user_agent})  # getting the review_url for an individual page
                    review_html = bs(revRes.text,features="html.parser")  # parsing the review page as HTML
                    commentboxes = review_html .find_all('article', {'class' : "-pvs -hr _bet"})
                    table = db[searchString] # creating a collection with the same name as search string. Tables and Collections are analogous.
                    #filename = searchString+".csv" #  filename to save the details
                    #fw = open(filename, "w") # creating a local file to save the details
                    #headers = "Product, Customer Name, Rating, Heading, Comment \n" # providing the heading of the columns
                    #fw.write(headers) # writing first the headers to file
                    reviews = []

                    for commentbox in commentboxes:
                        try:
                            name = commentbox.find_all('div')[2].div.find_all('span')[1].text
                        except:
                            name = 'No Name'

                        try:
                            rating =commentbox.div.text
                        except:
                            rating ='No Rating'

                        try:
                            commentDate = commentbox.find_all('div')[2].div.find_all('span')[0].text
                        except:
                            commentDate = 'No Comment Date'

                        try:
                            commentHead = commentbox.h3.text.lower()
                        except:
                            commentHead = 'No Comment Head'

                        try:
                            custComment = commentbox.p.text
                        except:
                            custComment = 'No Customer Comment'
                        #fw.write(searchString+","+name.replace(",", ":")+","+rating + "," + commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                        mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,"Comment": custComment} # saving that detail to a dictionary
                        #x = table.insert_one(mydict) #insertig the dictionary containing the rview comments to the collection
                        reviews.append(mydict) #  appending the comments to the review list

                    return render_template('results.html', reviews=reviews) # showing the review to the users
        except Exception as e:
            #print('something is wrong' )
            lg.error("An error occurred: %s", str(e))
            return 'something is wrong' + ' ' + str(e)
    else:
        return render_template('index.html')



# Run code Here
if __name__ == "__main__":
    app.run(port=8000,debug=True) # running the app on the local machine on port 8000
