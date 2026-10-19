# -*- coding: utf-8 -*-
{
    'name': "Multi Address POS",
    'summary': "Manage multiple delivery addresses in Point of Sale",
    'description': """
        Multi Address Management for Point of Sale
        - Select different delivery addresses during checkout
        - Add and edit customer addresses from POS
        - Integration with Peruvian receipts
    """,
    'author': "ACS",
    'website': "http://www.yourcompany.com",
    'category': 'Point of Sale',
    'version': '18.0.1.0.0',
    'depends': ['base', 'point_of_sale', 'l10n_pe_vat'],
    'data': [
        'views/res_partner_views.xml',
        'views/receipts.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'acs_multiaddress_pos_18/static/src/scss/pos.scss',
            'acs_multiaddress_pos_18/static/src/models/pos_store.js',
            'acs_multiaddress_pos_18/static/src/popups/select_direction_popup.js',
            'acs_multiaddress_pos_18/static/src/popups/select_direction_popup.xml',
            'acs_multiaddress_pos_18/static/src/popups/add_direction_popup.js',
            'acs_multiaddress_pos_18/static/src/popups/add_direction_popup.xml',
            'acs_multiaddress_pos_18/static/src/popups/edit_direction_popup.js',
            'acs_multiaddress_pos_18/static/src/popups/edit_direction_popup.xml',
            'acs_multiaddress_pos_18/static/src/overrides/partner_list_screen.js',
            'acs_multiaddress_pos_18/static/src/app/navbar.js',
            'acs_multiaddress_pos_18/static/src/app/navbar.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
