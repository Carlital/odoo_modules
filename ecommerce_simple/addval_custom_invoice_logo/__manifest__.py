# -*- coding: utf-8 -*-
{
   'name': "Logo opcional para facturas ",

    'summary': """
        Se establece un logo distinto para ventas de una cuenta analítica específica""",

    'description': """
        Para las facturas que tengan una orden de venta con la cuenta analítica N2Growth cambiará el logo de dicha marca
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Account",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': [
        'base',
        'addval_accounting'
    ],

    'data': [
        #'security/ir.model.access.csv',
        'views/res_company.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}