# doing necessary imports
import logging
from datetime import datetime
from flask import Flask, render_template, request
# from flask import Flask, render_template, request,jsonify
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
# from urllib.request import urlopen as uReq, Request
import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO, filename='logfile.txt', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)
today_date = datetime.today().strftime('%Y-%m-%d')
# Specify your browser's user agent string
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
app = Flask(__name__)  # initialising the flask app with the name 'app'




@app.route('/',methods= ['POST','GET'])
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            db = dbConn['crawlerDB']             # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            reviews_list = list(reviews)
            if len(reviews_list) > 0:  # if there are documents in the collection
                return render_template('results.html', reviews=reviews_list)
            else:
                # Append today's date to the filename
                reviews_list = []
                current_page = 1
                total_pages = 2
                url = "https://www.jumia.com.ng"
                filename = searchString + "_" + today_date + ".csv"
                fw = open(filename, "a")  # creating a local file to save the details
                headers = "Product, Customer Name, Rating, Heading, Comment \n"  # providing the heading of the columns
                fw.write(headers)
                table = db[searchString]  # creating a collection with the same name as search string. Tables and Collections are analogous.
                while current_page <= total_pages:
                    page_url = "https://www.jumia.com.ng/catalog/?q=" + searchString + "&page=" + str(current_page)
                    lg.info("Page %s is available", current_page)  # Log the message with the page number
                    # Create a Request object with the URL and headers
                    url_page = requests.get(page_url, headers={'User-Agent': user_agent})
                    # Read the content of the response
                    page_html = bs(url_page.content, "html.parser")  # parsing the webpage as HTML
                    bigboxes = page_html.findAll("article", {"class": "prd _fb col c-prd"})  # searching for appropriate tag to redirect to t
                    del bigboxes[0:3]  # the first 3 members of the list do not contain relevant information, hence deleting them.
                    box = bigboxes[0]   # taking the first iteration (for demo)
                    for box in bigboxes:
                        productLink = url + box.findAll('a')[1]['href']
                        prodRes = requests.get(productLink, headers={'User-Agent': user_agent})    # getting the product page from serve
                        prod_html = bs(prodRes.text, features="html.parser")  # parsing the product page as HTML


                        try:
                            reveiw_section = prod_html.find_all("section", {"class": "card aim -mtm"})
                            productAllReviewLink = "https://www.jumia.com.ng" + reveiw_section[0].find('a')['href']
                            revRes = requests.get(productAllReviewLink, headers={'User-Agent': user_agent})  # getting the review_url for
                            review_html = bs(revRes.text, features="html.parser")  # parsing the review page as HTML
                            commentboxes = review_html .find_all('article', {'class': "-pvs -hr _bet"})
                        except Exception as e:
                            commentboxes = prod_html .find_all('article', {'class': "-pvs -hr _bet"})

                        for commentbox in commentboxes:
                            try:
                                name = commentbox.find_all('div')[2].div.find_all('span')[1].text
                                name = name[3:]
                                lg.info("Success! name is available")
                            except Exception as e:
                                name = 'No Name'
                                lg.info("No name is available", str(e))

                            try:
                                rating = commentbox.div.text
                                rating = rating[0]
                                lg.info("Success! rating is available")
                            except Exception as e:
                                rating = 'No Rating'
                                lg.info("No rating is available")

                            try:
                                commentDate = commentbox.find_all('div')[2].div.find_all('span')[0].text
                                lg.info("Success! comment date  is available")
                            except Exception as e:
                                commentDate = 'No Comment Date'
                                lg.info("No comment date is available", str(e))

                            try:
                                commentHead = commentbox.h3.text.lower()
                                lg.info("Success! comment header  is available")
                            except Exception as e:
                                commentHead = 'No Comment Head'
                                lg.info("No comment head is available", str(e))

                            try:
                                custComment = commentbox.p.text
                                lg.info("Success! comment is available")
                            except Exception as e:
                                custComment = 'No Customer Comment'
                                lg.info("No customer comment is available")

                            fw.write(searchString+","+name.replace(",", ":")+","+rating + "," + commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                            mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead, "Comment": custComment}  # saving that detail to a dictionary
                            x = table.insert_one(mydict)  # insert the dictionary containing the review comments to the collection
                            reviews_list.append(mydict)  # appending the comments to the review list
                    current_page = current_page + 1

                return render_template('results.html', reviews=reviews_list)  # showing the review to the users
        except Exception as e:
            # print('something is wrong' )
            lg.error("An error occurred: %s", str(e))
            return 'something is wrong' + ' ' + str(e)
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)  # running the app on the local machine on port 8000

