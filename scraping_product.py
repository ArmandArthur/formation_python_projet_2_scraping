# coding: utf-8
#!/usr/bin/python3

import requests
import re
from bs4 import BeautifulSoup
from prettytable import PrettyTable

class Product:

    def __init__(self, uri):
        #Conself.format_stringuctor
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri
        self.file = "soup.txt"
        self.csv = 'product.csv'

    def import_product(self):
        response = requests.get(self.url_base+self.uri)
        if response.ok:
            # Write in file
            f = open(self.file, "w")
            f.write(response.text)
            f.close()

            # Open file
            fp = open(self.file, "r")
            soup = fp.read()
            fp.close()

            # Soup
            soup = BeautifulSoup(soup, 'lxml')

            # Variables  CSV
            product_page_url = self.url_base+self.uri
            product_page_url = self.format_string(product_page_url)

            title = soup.find('title').string
            title = self.format_string(title)

            upc = soup.find('table', class_="table-striped").findAll('tr')[0].find('td').text
            upc = self.format_string(upc)

            price_excluding_tax = soup.find('table', class_="table-striped").findAll('tr')[2].find('td').text
            price_excluding_tax = self.format_string(price_excluding_tax)

            price_including_tax = soup.find('table', class_="table-striped").findAll('tr')[3].find('td').text
            price_including_tax = self.format_string(price_including_tax)

            number_available_td = soup.find('table', class_="table-striped").findAll('tr')[5].find('td').text
            # Regex digital
            number_available_liste = re.findall(r'\d+', number_available_td)
            number_available = number_available_liste[0]
            number_available = self.format_string(number_available)

            product_description = soup.find('div', id="product_description").find_next_siblings('p')[0].text
            product_description = self.format_string(product_description)

            category = self.uri.split('/')[0]
            category = self.format_string(category)

            review_rating = soup.find('table', class_="table-striped").findAll('tr')[6].find('td').text
            review_rating = self.format_string(review_rating)

            image_src = soup.find('div', id="product_gallery").find('img')['src']
            image_src_split = image_src.split('/')
            # First ..
            del image_src_split[0]
            # Second ..
            del image_src_split[0]
            image_url = self.url_base+"/".join(image_src_split)
            image_url = self.format_string(image_url)

            # Write CSV
            t = PrettyTable()
            t.field_names = ['product_page_url', 'title', 'upc', 'price_including_tax', 'price_excluding_tax', 'number_available', 'product_description', 'category', 'review_rating', 'image_url']
            t.align='c'
            t.border=True
            t.add_row([product_page_url, title, upc, price_including_tax, price_excluding_tax, number_available, product_description, category, review_rating, image_url])
            f = open(self.csv, "w")
            f.write(str(t))
            f.close()
    def format_string(self, value):
        return str(value).strip()

product = Product('catalogue/the-four-agreements-a-practical-guide-to-personal-freedom_970/index.html');
product.import_product()