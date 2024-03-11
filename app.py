from flask import Flask, render_template, request
import requests
import os
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import pymongo
import csv

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            mongo_username = os.getenv('MONGODBUSERNAME')
            mongo_password = os.getenv('MONGODBPASSWORD')

            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            print(prod_html)
            commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})

            filename = searchString + ".csv"
            headers = "Product, Customer Name, Rating, CommentHead, Comment \n"
            reviews = []

            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                except:
                    name = 'No Name'

                try:
                    rating = commentbox.div.div.div.div.text
                except:
                    rating = 'No Rating'

                try:
                    commentHead = commentbox.div.div.div.p.text
                except:
                    commentHead = 'No Comment Heading'

                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    custComment = 'No Comment'

                mydict = {
                    "Product": searchString,
                    "Name": name,
                    "Rating": rating,
                    "CommentHead": commentHead,
                    "Comment": custComment
                }
                reviews.append(mydict)



            with open(filename, "a", newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Product", "Name", "Rating", "CommentHead", "Comment"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if csvfile.tell() == 0:  # Check if the file is empty
                    writer.writeheader()

            # Append data to the CSV file only if Name and Comment are not missing
                for review in reviews:
                    if review["Name"] != "No Name" and review["Comment"] != "No Comment":
                        writer.writerow(review)

            logging.info("Logged {} reviews to CSV.".format(len(reviews)))


            client = pymongo.MongoClient(
                "mongodb+srv://" + mongo_username + ":" + mongo_password +
                "@cluster0.j3wnbpo.mongodb.net/?retryWrites=true&w=majority")
            db = client['review_scrap']
            review_col = db['review_scrap_data']
            review_col.insert_many(reviews)
            return render_template('result.html', reviews=reviews[0:(len(reviews) - 1)])
        except Exception as e:
            logging.error("Error: {}".format(str(e)))
            return 'something is wrong'

    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
