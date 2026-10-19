# -*- coding: utf-8 -*-
{
    'name': 'Pricelist Items Manager',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Easily manage and delete pricelist items in Odoo',
    'description': """
Pricelist Items Manager for Odoo 18
===================================

This module provides a dedicated menu to list all pricelist items with the ability to easily delete unwanted entries.

Key Features:
------------
* Dedicated menu for pricelist items under Sales > Products
* Comprehensive list view with all relevant fields
* Easy deletion of pricelist items
* Proper access rights management for sales managers

This module is perfect for:
-------------------------
* Cleaning up old or obsolete pricelist items
* Managing large numbers of pricelist entries
* Quickly finding and modifying pricelist rules

Fully compatible with Odoo 18 Community and Enterprise editions.
    """,
    'author': 'Ahmed Nour',
    'website': 'https://odoosa.net',
    'maintainer': 'Ahmed Nour',
    'images': ['static/description/banner.png'],
    'depends': ['product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pricelist_item_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'EUR',
    'support': 'ahmednour@outlook.com',
}
