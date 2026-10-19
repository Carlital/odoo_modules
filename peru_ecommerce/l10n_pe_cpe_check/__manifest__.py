# -*- coding: utf-8 -*-
{
    'name': "Cpe Check",

    'summary': """
        Cpe Check""",

    'description': """
        Cpe Check
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['l10n_pe_cpe'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/pe_check_cpe_data.xml',
        'views/account_move_views.xml',
    ],
}