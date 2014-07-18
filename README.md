

Pre-requis

  * Django 1.4 (? ; ne marche pas avec 1.6.x ; marku pdeprecated)
  * Module : cairo reportlab trml2pdf


Debian Wheezy : python-django python-cairo python-reportlab python-trml2pdf

Configruation :
  * fichier resarmll/settings_local.py

Initialisation de la base :

  * for m in auth contenttypes sessions sites messages staticfiles markup admin resautils resa compta account resaroom ; do python manage.py sql $m ; done > /tmp/resarmll.sql
  * donner le resarmll.sql a manger a la base
    * sqlite3 data/resarmll.db < /tmp/resarmll.sql
  * ajouter un enreigstrement dans django_site pour indiquer le domaine du site
  * creer l'admin :
    * python manage.py createsuperuser

  * donees a importer
    * pays dans misc/countries/countries.csv
     * python manage.py loaddata countries
     * charge a partir de ./resa/fixtures/countries.json
    * plan comptable dans misc/compta/plan-comptable.csv
