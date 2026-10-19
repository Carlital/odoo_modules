# -*- coding: utf-8 -*-
{
    'name': "Datos desde venta a factura",

    'summary': """
        Módulo que pasa datos necesarios para la factura desde la venta""",

    'description': """
        Este módulo pasa los siguientes datos desde la venta a la factura:
        - OC (orden de compra)
        - HES 
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base','account','sale_management'],

    'data': [
        #'views/account_move.xml',
        #'views/sale_order.xml',
        #'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}