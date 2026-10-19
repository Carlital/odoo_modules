# -*- coding: utf-8 -*-
{
   'name': "Agrupación Productos por Marcas",

    'summary': """
        Agrupación Productos por Marcas (addval_brand_agroupation)""",

    'description': """
        Agrupación Productos por Marcas (addval_brand_agroupation)
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': [
        'base',
        'sale',
        'website_product_brands',
    ],

    'data': [
        'views/sale_report_views.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}