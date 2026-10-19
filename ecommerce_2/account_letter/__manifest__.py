# -*- coding: utf-8 -*-
{
    'name': "Account Letter",

    'summary': """
        Account, Letter""",

    'description': """
        Letters
    """,

    'author': "Cristhian Guachan",
    'website': "http://www.ejemplo.com",

    'category': 'Uncategorized',
    'version': '18.0.0.1',

    'depends': ['account','mail'],

    'data': [
        'security/ir.model.access.csv',
        "wizard/account_letter_payment_wizard_view.xml",
        'wizard/account_letter_wizard_view.xml',
        'wizard/letter_report_view.xml',
        'wizard/account_letter_returned_wizard_view.xml',
        'wizard/account_generate_letters.xml',
        'views/report_letter.xml',
        'data/letter_data.xml',
        'views/account_letter_view.xml',
        'views/account_view.xml',
        'views/res_partner.xml',
        'views/templates.xml',
        # 'report/letters_report.xml',        
    ],
    'license': 'LGPL-3',
}