# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS",

    'summary': """
        Peruvian Management POS""",

    'description': """
        Peruvian Management POS
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Localization/Peruvian',
    'version': '0.3',

    'depends': [
        'point_of_sale',
        'l10n_pe_pos',
        'l10n_pe_vat',
    ],

    'data': [
        'data/res_partner_data.xml',
    ],
    'assets': {
            'point_of_sale._assets_pos': [
                'l10n_pe_pos_extend/static/lib/NumeroALetras.js',
                'l10n_pe_pos_extend/static/src/overrides/**/*',
            ],
    },
}