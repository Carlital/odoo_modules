# -*- coding: utf-8 -*-
{
    'name': "Comunas por Región",

    'summary': """
        Comunas con dominio en regiones (addval_cl_communes)""",

    'description': """
        Comunas con dominio en regiones (addval_cl_communes)
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Partner",
    "license": "Other proprietary",
    'version': '0.1',
    
    'data': [
        'data/res_city.xml',
        'views/res_partner.xml',
    ],
    
    'depends': [
        'base', 
        'base_address_extended'
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
