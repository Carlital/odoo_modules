# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS Tickets",

    'summary': """
        Point of Sale""",

    'description': """
        Tickets from POS, for peruvian localization
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Localization/Peruvian',
    'version': '1.0',

    'depends': ['pos_sale', 'l10n_pe_pos_cpe'],

    'assets': {
            'point_of_sale._assets_pos': [
                'l10n_pe_pos_ticket/static/src/**/*'
            ],
    },
}