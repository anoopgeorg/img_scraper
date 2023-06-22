from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import urllib.request
import time
from pymongo.mongo_client import MongoClient
import os


logging.basicConfig(filename="img_scrapper.log" , level=logging.INFO)

app = Flask(__name__)



@app.route("/", methods = ['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")

def connectToMongo():
    uri = "mongodb+srv://anoopgeorge:kiuHFSiLpW7mOyed@cluster0.jlvs1rq.mongodb.net/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client = MongoClient(uri)
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        logging.info("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        logging.error(e)      
    return client     

@app.route("/image_dump" , methods = ['POST' , 'GET'])
@cross_origin()
def imageDump():
    if request.method == 'POST':
        save_dir = 'Images/'
        # Create Local DIR
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            logging.info("Directory Created ----->" + str(save_dir))

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'accept-language': 'en-GB,en;q=0.9',}
        searchString = request.form['content'].replace(" ","")
        app.logger.info(request.form['content'])        
        app.logger.info(searchString)
        search_url = "https://www.google.com/search?q=" + searchString
        req = urllib.request.Request(url=search_url,headers=headers)
        logging.info("Image search link ----->" + str(search_url))


        try:
            searchResult = uReq(req)
            logging.info("URLOPEN Called from -----> /image_dump")
            searchResustBs = bs(searchResult,'html.parser')
            images = searchResustBs.find_all('img')
            img_links = [link['src'] for link in images]
            
            imageDumpList = []
            for i,img_link in enumerate(img_links):
                try:
                    img_data = requests.get(img_link).content
                    img_set = {
                        "Image_index":i,
                        "Image_link":img_link,
                        "Image_data":img_data
                    }
                    imageDumpList.append(img_set)

                    # write image to local dir
                    with open(os.path.join(save_dir, f"{searchString}_{i}.jpg"), "wb") as f:
                        f.write(img_data)                 
                    
                except Exception as e:
                    logging.error(e)
            if imageDumpList is not None:
                mongo_client = connectToMongo()
                image_scraper_db = mongo_client['image_scraper_db']
                image_scraper_coll = image_scraper_db['image_scraper_coll']
                try:
                    logging.info("Push to MongoDB initiated ----->")
                    image_scraper_coll.insert_many(imageDumpList)
                    logging.info("Push to MongoDB completed ----->")
                except Exception as e:
                    logging.error("Push to MongoDB failed with error ----->")
                    logging.error(e)
                    









        except Exception as e:
            message ='Something went wrong!'
            logging.error(message)
            logging.error(e)
            return render_template('result.html',msg=message)

        mongo_client = connectMongo()
        for product in product_Links:
            logging.info("Product parser---> {}".format(product))
            product_review = {}
            result = get_customer_reviews(product)
            if result is not None:
                product, customer_rev_boxes = result
                if customer_rev_boxes is not None:
                    customer_review_list = get_customer_details(product,customer_rev_boxes)
                    if customer_review_list is not None:
                        product_review_list = product_review_list + customer_review_list
        scraper_db = mongo_client['scraper_db']
        amazon_collection = scraper_db['amazon_collection']
        final_result = {"searchString" : searchString,
                        "product_review_list" : product_review_list
                        }
        logging.info("Push to mongoDB intiated")
        try:
            amazon_collection.insert_one(final_result)
        except Exception as e:
            logging.error(e)
        logging.info("Push to mongoDB completed")
        logging.info("log my final result {}".format(product_review_list))
        logging.shutdown()
        return render_template('result.html',reviews= product_review_list)
    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0",debug=True)
