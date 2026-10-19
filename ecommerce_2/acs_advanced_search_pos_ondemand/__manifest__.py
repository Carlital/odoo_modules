# -*- coding: utf-8 -*-
{
    'name': 'ACS Advanced Search POS On Demand',
    'summary': 'Carga productos del POS bajo demanda usando la búsqueda avanzada de ACS',
    'version': '18.0.2.0.0',
    'category': 'Point of Sale',
    'author': 'Carla Lomas',
    'license': 'LGPL-3',
    'depends': ['acs_advanced_search', 'point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_advanced_search_pos_ondemand/static/src/js/product_many2x_search_patch.js',
        ],
        'point_of_sale._assets_pos': [
            'acs_advanced_search_pos_ondemand/static/src/pos/product_screen.js',
        ],
    },
    'installable': True,
    'application': False,
}
