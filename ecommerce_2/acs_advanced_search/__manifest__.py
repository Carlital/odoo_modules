# -*- coding: utf-8 -*-
{
    'name': "ACS advanced search ",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'sequence': 20,
    'description': """
        Long description of module's purpose
    """,

    'author': "Cristhian Guachán",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['purchase','base','sale','account','point_of_sale','sale_management'],
    #
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_advanced_search/static/src/js/*',
        ],
        'point_of_sale._assets_pos': [
            'acs_advanced_search/static/src/pos/*',
        ],
    },
    'license': 'LGPL-3',
   
}