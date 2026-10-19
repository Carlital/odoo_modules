# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS CPE",

    'summary': """
        POS, CPE""",

    'description': """
        Peruvian Management POS CPE
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Peruvian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'point_of_sale',
        'l10n_pe_cpe',
        'l10n_pe_pos_extend',
    ],

    # always loaded
    'data': [
        #'views/pos_order_view.xml',
        #'views/pos_config_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
            'point_of_sale._assets_pos': [
                'l10n_pe_pos_cpe/static/lib/Blob.js',
                'l10n_pe_pos_cpe/static/lib/FileSaver.js',
                'l10n_pe_pos_cpe/static/lib/qrious.js',
                'l10n_pe_pos_cpe/static/lib/String.js',
                'l10n_pe_pos_cpe/static/src/overrides/models/db.js',
                'l10n_pe_pos_cpe/static/src/overrides/models/pos_store.js',
                'l10n_pe_pos_cpe/static/src/overrides/models/models.js',
                'l10n_pe_pos_cpe/static/src/overrides/components/payment_screen/payment_screen.js',
                'l10n_pe_pos_cpe/static/src/overrides/components/payment_screen/payment_screen.xml',
                'l10n_pe_pos_cpe/static/src/overrides/components/receipt/order_receipt.xml',
                'l10n_pe_pos_cpe/static/src/overrides/components/receipt/receipt_header.xml',
            ],
    },
    # 'assets': {
    #         'point_of_sale.assets': [
    #         'l10n_pe_pos_cpe/static/src/lib/Blob.js',
    #         'l10n_pe_pos_cpe/static/src/lib/FileSaver.js',
    #         'l10n_pe_pos_cpe/static/src/lib/qrcode.js',
    #         'l10n_pe_pos_cpe/static/src/lib/qrious.js',
    #         'l10n_pe_pos_cpe/static/src/lib/qrcode.js',
    #         'l10n_pe_pos_cpe/static/src/js/models.js',
    #         'l10n_pe_pos_cpe/static/src/js/db.js',
    #         'l10n_pe_pos_cpe/static/src/js/Screens/PaymentScreen/PaymentScreen.js',
    #         #'l10n_pe_pos_cpe/static/src/js/Screens/OrderReceipt.js',
    #         'l10n_pe_pos_cpe/static/src/js/Screens/TicketScreen/TicketScreen.js',
    #         'l10n_pe_pos_cpe/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
    #         'l10n_pe_pos_cpe/static/src/xml/Screens/PaymentScreen/PaymentScreen.xml'
    #     ],
    # },
}