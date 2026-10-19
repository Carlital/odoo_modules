# -*- coding: utf-8 -*-
{
    'name': "acs_pos_with_sale",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','pos_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'assets': {
        'point_of_sale._assets_pos': [
            'acs_pos_with_sale/static/src/**/*',
        ],
    },
}
