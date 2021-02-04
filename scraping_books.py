"""
   Module scraping
"""
# coding: utf-8
#!/usr/bin/python3
import urllib.request
import os
import re
import errno
import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable

class Product:
    """
        Return une liste avec les valeurs des attributs du produit
    """
    def __init__(self, uri, category_name):
        """
            Variables de classe: instance
        """
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri
        self.file = "soup.txt"
        self.category_name = category_name
        self.v_html = {}
        self.response_request = ''
        self.soup = ''
    def import_product(self):
        """
            Requête sur l'url
            Sauvegarde dans un fichier
            Parse le fichier et extraits les valeurs des balises HTML.
            Sauvegarde l'image dans le bon dossier
            Retourne une liste
        """
        request_url = str(self.url_base)+str(self.uri)
        print(request_url)
        self.response_request = requests.get(request_url)
        self.response_request = self.response_request.text.encode('utf8').decode('ascii', 'ignore')

        # Write in file
        f_write = open(self.file, "w")
        f_write.write(self.response_request)
        f_write.close()

        # Open file
        f_open = open(self.file, "r")
        self.soup = f_open.read()
        f_open.close()

        # Soup
        self.soup = BeautifulSoup(self.soup, 'lxml')

        # Variables  CSV
        self.v_html['product_page_url'] = self.f_string(self.url_base+self.uri)
        self.v_html['title'] = self.f_string(self.soup.find('title').string)

        table_striped = self.soup.find('table', class_="table-striped")
        trs = table_striped.findAll('tr')

        self.v_html['upc'] = self.f_string(trs[0].find('td').text)
        self.v_html['price_excluding_tax'] = self.f_string(trs[2].find('td').text)
        self.v_html['price_including_tax'] = self.f_string(trs[3].find('td').text)

        nb_stock_td = table_striped.findAll('tr')[5].find('td').text
        # Regex digital
        nb_stock_liste = re.findall(r'\d+', nb_stock_td)
        self.v_html['nb_stock'] = self.f_string(nb_stock_liste[0])

        if self.soup.find('div', id="product_description"):
            self.v_html['p_desc'] = self.soup.find('div', id="product_description")
            self.v_html['p_desc'] = self.v_html['p_desc'].find_next_siblings('p')[0].text
            self.v_html['p_desc'] = self.f_string(self.v_html['p_desc'])
        else:
            self.v_html['p_desc'] = ''

        self.v_html['category'] = self.category_name

        self.v_html['review_rating'] = trs[6].find('td').text
        self.v_html['review_rating'] = self.f_string(self.v_html['review_rating'])

        image_src = self.soup.find('div', id="product_gallery").find('img')['src']
        image_src_split = image_src.split('/')
        # First ..
        del image_src_split[0]
        # Second ..
        del image_src_split[0]
        self.v_html['image_url'] = self.url_base+"/".join(image_src_split)
        self.v_html['image_url'] = self.f_string( self.v_html['image_url'])

        # Download Image
        title_image = os.path.basename(self.v_html['image_url'])
        path_folder = 'books/images/'+self.category_name+"/"
        path_file = path_folder+title_image
        if not os.path.exists(path_folder):
            try:
                os.makedirs(os.path.dirname(path_folder))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        urllib.request.urlretrieve(self.v_html['image_url'], path_file)

        return [self.v_html['product_page_url'],
                self.v_html['title'],
                self.v_html['upc'],
                self.v_html['price_including_tax'],
                self.v_html['price_excluding_tax'],
                self.v_html['nb_stock'],
                self.v_html['p_desc'],
                self.v_html['category'],
                self.v_html['review_rating'],
                self.v_html['image_url']]
    def f_string(self, value):
        """
            Retire espace
        """
        return str(value).strip()


class Category:
    """
        Ajoute les donnness retourner par la classe product dans une liste
    """
    def __init__(self, uri, category_name):
        self.url_base = 'http://books.toscrape.com/'
        self.uri = uri
        self.products_datas = []
        self.next_page = ''
        self.category_name = category_name

    def products_extract(self):
        """
            Requete
            Cherche les liens des produits
            Ajoute à la liste les données du produit trouvé
            Prends en compte la pagination
        """
        response_request = requests.get(self.url_base+self.uri)
        if response_request.ok:
            # Soup
            soup = BeautifulSoup(response_request.text, 'lxml')

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
    """
        1 scraping par page
        while pour la pagination
    """
    def __init__(self, csv_folder, csv_path, category_path, category_name):
        self.url_base = 'http://books.toscrape.com/'
        self.categorie_current = ""
        self.csv = csv_folder+'/'+csv_path
        self.global_datas = {} #dictionnaire
        self.category_path = category_path
        self.category_name = category_name

    def initialisation(self):
        """
            Init
        """
        pagination = 1
        self.categorie_current = Category(self.category_path, self.category_name)
        self.categorie_current.products_extract()
        self.global_datas[pagination] = self.categorie_current.products_datas
        while self.categorie_current.next_page != '':
            # Delete the last part
            category_path_split = self.category_path.split('/')
            del category_path_split[len(category_path_split)-1]
            self.category_path = "/".join(category_path_split)
            uri = self.category_path+'/'+self.categorie_current.next_page
            self.categorie_current = Category(uri, self.category_name)
            self.categorie_current.products_extract()
            pagination = pagination + 1
            self.global_datas[pagination] = self.categorie_current.products_datas

        #print(self.global_datas)
        t_pretty = PrettyTable()
        t_pretty.field_names = ['pagination',
        'product_page_url',
        'title',
        'upc',
        'price_including_tax',
        'price_excluding_tax',
        'number_available',
        'product_description',
        'category',
        'review_rating',
        'image_url']
        t_pretty.align='l'
        t_pretty.border=True
        for pagination, products in self.global_datas.items():
            for product in products:
                product.insert(0, pagination)
                t_pretty.add_row(product)
        if not os.path.exists(os.path.dirname(self.csv)):
            try:
                os.makedirs(os.path.dirname(self.csv))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        f_open = open(self.csv+'_'+self.category_name+'.csv', "w")
        f_open.write(str(t_pretty))
        f_open.close()

response = requests.get('http://books.toscrape.com/index.html')
if response.ok:
    soup_beautiful = BeautifulSoup(response.text, 'lxml')
    category = soup_beautiful.find('ul', class_="nav-list" ).find('li')
    link_categories = category.find('ul').find_all('a')
    for link_category in link_categories:
        href = link_category['href']
        category_name_global = link_category.text.strip()
        scrap = Scraping('books', 'csv_books', href, category_name_global)
        scrap.initialisation()
