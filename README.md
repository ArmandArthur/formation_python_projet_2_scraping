# Projet Scraping

1) Installer un environnement virtuel
https://docs.python.org/fr/3/library/venv.html

2) Installer des dépendances: 
pip install -r requirements.txt

3) Extrait dans un CSV les données d'un produit (racine projet): 
py scraping_product.py

4) Extrait dans un CSV tous les produits d'une catégorie (dossier category) avec pagination: 
py scraping_category.py

5) Extraites dans des CSV distincts tous les produits de toutes les catégories (dossier books) avec pagination: 
py scraping_books.py