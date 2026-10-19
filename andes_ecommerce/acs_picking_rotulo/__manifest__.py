# -*- coding: utf-8 -*-
{
    'name': "ACS Rotulo en Picking",

    'summary': """Letter pdf in stock_picking """,

    'description': """
        Letter pdf in stock_picking 
    """,

    'author': "Cristhian Guachán",
    'website': "",
    'category': 'Uncategorized',
    'version': '17.0.0.1',

    'depends': [
        'stock','contacts'
        ],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'license': 'LGPL-3',
}