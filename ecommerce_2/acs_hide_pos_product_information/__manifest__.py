# -*- coding: utf-8 -*-
{
    'name': "ACS hide pos product information",

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
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        
    ],
   'assets': {

        # PoS assets

        # Main PoS assets, they are loaded in the PoS UI and in the PoS unit tests
        'point_of_sale._assets_pos': [
            # 'preparation_display' bootstrap customization layer
            'acs_hide_pos_product_information/static/src/css/style.css',
        ]
   }
}

