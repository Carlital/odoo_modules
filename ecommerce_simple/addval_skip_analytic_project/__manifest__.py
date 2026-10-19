# -*- coding: utf-8 -*-
{
    'name': "Evitar creación de cuentas analíticas desde proyectos",

    'summary': """
        Módulo que salta la creación de cuentas analíticas desde proyectos""",

    'description': """
        Este módulo permite evitar la creación de cuentas analíticas cada vez que se crea un proyecto, desde el mismo módulo o desde el módulo de ventas
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base','account','sale_management', 'project'],

    'data': [
        #'views/account_move.xml',
        'views/project.xml',
        #'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}