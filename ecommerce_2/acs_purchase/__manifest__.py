# -*- coding: utf-8 -*-
{
    'name': "ACS Purchase",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'purchase_last_price_info'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/res_partner_views.xml',

        # Wizard

        'wizard/list_price_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'acs_purchase/static/src/css/custom.css',
        ],
    },
}
