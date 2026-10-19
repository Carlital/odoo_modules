# -*- coding: utf-8 -*-
{
    'name': "Peruvian Report",

    'summary': """
        Report, Account""",

    'description': """
        Invoice Reports
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'l10n_pe_cpe', 'report_xlsx',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_report_wizard_view.xml',
        'views/invoice_report_view.xml',
        #'views/report_templates.xml',
    ],
}