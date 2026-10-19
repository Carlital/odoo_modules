# -*- coding: utf-8 -*-
{
   'name': "Cuenta Analítica Pedidos Web",

    'summary': """
        Cuenta Analítica Pedidos Web (addval_website_sale)""",

    'description': """
        Cuenta Analítica Pedidos Web (addval_website_sale)
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Sale",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': [
        'base',
        'sale',
        'portal',
        'website',
        'website_sale',
        'website_sale_delivery'
    ],

    'data': [
        'views/website.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}