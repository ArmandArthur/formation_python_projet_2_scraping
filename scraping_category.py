# coding: utf-8
#!/usr/bin/python3

import requests
import os
import re
from bs4 import BeautifulSoup
from prettytable import PrettyTable

class Product:

    def __init__(self, uri):
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri
        self.file = "soup.txt"

    def import_product(self):
        request_url = str(self.url_base)+str(self.uri)
        print(request_url)
        response = requests.get(request_url).text.encode('utf8').decode('ascii', 'ignore')
        # Write in file
        f = open(self.file, "w")
        f.write(response)
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

        return [product_page_url, title, upc, price_including_tax, price_excluding_tax, number_available, product_description, category, review_rating, image_url]
    
    def format_string(self, value):
        return str(value).strip()


class Category:
    
    def __init__(self, uri):
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri  
        self.products_datas = []
        self.next_page = ''

    def products_extract(self):
        response = requests.get(self.url_base+self.uri)
        if response.ok:
            # Soup
            soup = BeautifulSoup(response.text, 'lxml')

            # Search articles
            articles = soup.find_all('article', class_="product_pod" )
            for article in articles:
                link = article.find('h3').find('a')['href']
                # Remove .. relative path
                link_split = link.split('/')
                del link_split[0]
                del link_split[0]
                del link_split[0]
                link = "/".join(link_split)
                product = Product('catalogue/'+link)
                self.products_datas.append(product.import_product())
            #return self.products_datas

            if soup.find('li', class_="next"):
                next_page = soup.find('li', class_="next").find('a')['href']
                self.next_page = str(next_page)

class Scraping:

    def __init__(self):
        self.url_base = 'http://books.toscrape.com/'
        self.categorie_current = ""
        self.csv = 'category/csv_category.csv'    
        self.global_datas = {} #dictionnaire

    def initialisation(self):
        pagination = 1
        self.categorie_current = Category('catalogue/category/books/nonfiction_13')
        self.categorie_current.products_extract()
        self.global_datas[pagination] = self.categorie_current.products_datas
        while self.categorie_current.next_page != '':
            self.categorie_current = Category('catalogue/category/books/nonfiction_13/'+self.categorie_current.next_page)
            self.categorie_current.products_extract()
            pagination = pagination + 1
            self.global_datas[pagination] = self.categorie_current.products_datas    

        #print(self.global_datas)
        t = PrettyTable()
        t.field_names = ['pagination', 'product_page_url', 'title', 'upc', 'price_including_tax', 'price_excluding_tax', 'number_available', 'product_description', 'category', 'review_rating', 'image_url']
        t.align='l'
        t.border=True
        for pagination, products in self.global_datas.items():
            for product in products:
                product.insert(0, pagination)
                t.add_row(product)
        if not os.path.exists(os.path.dirname(self.csv)):
            try:
                os.makedirs(os.path.dirname(self.csv))
            except OSError as exc: 
                if exc.errno != errno.EEXIST:
                    raise
        f = open(self.csv, "w")
        f.write(str(t))
        f.close()

scrap = Scraping()
scrap.initialisation()