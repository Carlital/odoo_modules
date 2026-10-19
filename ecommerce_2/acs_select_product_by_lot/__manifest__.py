# -*- coding: utf-8 -*-
{
    'name': 'ACS Select Product By Lot',
    'version': '18.0.1.0.0',
    'summary': 'Selecciona lotes/series disponibles en líneas de producción',
    'category': 'Manufacturing',
    'author': 'Juan Ayala',
    'website': '',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
