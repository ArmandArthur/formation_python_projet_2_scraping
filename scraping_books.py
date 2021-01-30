# coding: utf-8
#!/usr/bin/python3

import requests
import os
import re
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import urllib.request

class Product:

    def __init__(self, uri, category_name):
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri
        self.file = "soup.txt"
        self.category_name = category_name

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

        if soup.find('div', id="product_description"):
            product_description = soup.find('div', id="product_description").find_next_siblings('p')[0].text
            product_description = self.format_string(product_description)
        else:
            product_description = ''

        category = self.category_name

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

        # Download Image
        title_image = os.path.basename(image_url)
        path_folder = 'books/images/'+self.category_name+"/"
        path_file = path_folder+title_image
        if not os.path.exists(path_folder):
            try:
                os.makedirs(os.path.dirname(path_folder))
            except OSError as exc: 
                if exc.errno != errno.EEXIST:
                        raise
        urllib.request.urlretrieve(image_url, path_file)

        return [product_page_url, title, upc, price_including_tax, price_excluding_tax, number_available, product_description, category, review_rating, image_url]
    
    def format_string(self, value):
        return str(value).strip()


class Category:
    
    def __init__(self, uri, category_name):
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri  
        self.products_datas = []
        self.next_page = ''
        self.category_name = category_name

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
                product = Product('catalogue/'+link, self.category_name)
                self.products_datas.append(product.import_product())

            if soup.find('li', class_="next"):
                next_page = soup.find('li', class_="next").find('a')['href']
                self.next_page = str(next_page)

class Scraping:

    def __init__(self, csv_folder, csv_path, category_path, category_name):
        self.url_base = 'http://books.toscrape.com/'
        self.categorie_current = ""
        self.csv = csv_folder+'/'+csv_path    
        self.global_datas = {} #dictionnaire
        self.category_path = category_path
        self.category_name = category_name

    def initialisation(self):
        pagination = 1
        self.categorie_current = Category(self.category_path, self.category_name)
        self.categorie_current.products_extract()
        self.global_datas[pagination] = self.categorie_current.products_datas
        while self.categorie_current.next_page != '':
            # Delete the last part
            category_path_split = self.category_path.split('/')
            del category_path_split[len(category_path_split)-1]
            self.category_path = "/".join(category_path_split)
            print(self.category_path+'/'+self.categorie_current.next_page)
            self.categorie_current = Category(self.category_path+'/'+self.categorie_current.next_page, self.category_name)
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
        f = open(self.csv+'_'+self.category_name+'.csv', "w")
        f.write(str(t))
        f.close()

response = requests.get('http://books.toscrape.com/index.html')
if response.ok:
    soup = BeautifulSoup(response.text, 'lxml')
    category = soup.find('ul', class_="nav-list" ).find('li')
    links = category.find('ul').find_all('a')
    for link in links:
        href = link['href']
        category_name = link.text.strip()
        scrap = Scraping('books', 'csv_books', href, category_name)
        scrap.initialisation()