import json
import requests
from bs4 import BeautifulSoup
import argparse
import pandas

class WebScraper:
    def __init__(self, address):
        self.address = address
    
    # Input the address
    def geocoding(self):
        api_key = "" #Enter your api key before use
        # Set the parameters of the request
        params = {
            "address": self.address,
            "key": api_key,
        }
        # Send a request to Google geocoding
        response = requests.get(url="https://maps.googleapis.com/maps/api/geocode/json", params=params)
        address_info_b = response.content #format byte
        address_info_js = address_info_b.decode()
        address_info = json.loads(address_info_js)
        self.zipcode = address_info["results"][0]["address_components"][6]["long_name"] # Extract zipcode from json file
        print ("Searching zipcode:" + self.zipcode)
        
    # Input the zipcode of the target region
    def get_houses(self):
        # Add headers in case the system identify you as a robot
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'}
        # Send a request to REDFIN
        response = requests.get(url="https://www.redfin.com/zipcode/%s" % self.zipcode, headers=self.headers)
        with open('redfinZipcode_webpage.html', 'w', encoding="utf-8") as house_file:
            house_file.write(response.text)
        print("Webpage saved")
        print("Searching house information...")
        with open('redfinZipcode_webpage.html', 'r', encoding="utf-8") as html:
            self.webpage = html.read()
        # Parse the webpage
        soup = BeautifulSoup(self.webpage, 'html.parser')
        # Get the information of houses from the html
        self.house_collection = []
        all_houses_info = soup.find_all("div", class_="bottomV2")
        house_urls = soup.find_all("a", {"class":"slider-item"})
        for h in all_houses_info:
            # Get house information
            price = h.find('span', class_="homecardV2Price").string
            address = h.find('span', {"data-rf-test-id": "abp-streetLine"}).string
            api_key = "" #Enter your api key before use
            # Set the parameters of the request
            params = {
                "address": str(address),
                "key": api_key,
            }
            response = requests.get(url="https://maps.googleapis.com/maps/api/geocode/json", params=params)
            # Get the coordinates from the response
            data = json.loads(response.text)
            lat = data["results"][0]["geometry"]["location"]["lat"]
            lng = data["results"][0]["geometry"]["location"]["lng"]
            coordinate = [lat, lng]
            self.house_collection.append([price, address, coordinate])
        for i, elem in enumerate(house_urls):
            sub_addr = elem.get('href')
            house_url = "https://www.redfin.com/%s" % sub_addr
            self.house_collection[i].append(house_url)
        print("House information saved")

    
    # Save house information
    def save_houses(self):
        print("Saving house images...")
        for i, data in enumerate(self.house_collection):
            hp_response = requests.get(url= data[3], headers=self.headers)
            self.house_page = hp_response.content
            image_soup = BeautifulSoup(self.house_page, 'html.parser')
            house_img_info = image_soup.find_all('img', class_="landscape")
            house_img_url = house_img_info[0]['src']
            self.house_collection[i].append(house_img_url)
            response_img = requests.get(url=house_img_url)
            with open("%s_image_for %s_house.jpg" % (i,self.house_collection[i][0]), "wb") as house_img:
                house_img.write(response_img.content)
        print("All house Photos have been saved.")
        house = House()
        house.save_house_info(self.house_collection) # Save house information as file
        print("House information file created")
        
        
              
class House(WebScraper):
    def __init__(self):
        # Set house attributes
        pass
    
    def save_house_info(self, data):
        self.data = data
        price_collection   = []
        address_collection = []
        coord_collecion    = []
        url_collection = []
        image_url_colleciton = []
        for i in range(len(self.data)):
            price_collection.append(self.data[i][0])
            address_collection.append(self.data[i][1])
            coord_collecion.append(self.data[i][2])
            url_collection.append(self.data[i][3])
            image_url_colleciton.append(self.data[i][4])
        dict = {"House Price": price_collection, "House Address": address_collection, "Coordinates[lat, lng]":coord_collecion, "House url":url_collection, "House Image url":image_url_colleciton}
        df = pandas.DataFrame(data = dict)
        df.to_csv("HouseList.csv", index=True)

            
        

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description='Process some parameters.')
    parser.add_argument('-a', '--address', type = str, help='a valid address in string type')
    args = parser.parse_args()

    
    web_scraper = WebScraper(args.address) # Create a webscraper instance 
    web_scraper.geocoding() # Send the address to the webscraper 
    web_scraper.get_houses() # Collect a set of houses and their information
    web_scraper.save_houses() # Save house information into files
    print("End program")
