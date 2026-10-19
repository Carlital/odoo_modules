# -*- coding: utf-8 -*-
{
    'name': "Peruvian Invoice",

    'summary': """
        Peruvian Invoice""",

    'description': """
        Peruvian Invoice
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.3',
    'depends': [
        'account',
        'uom',
        'account_debit_note',
        #'account_fiscal_year',
        #'sequence_reset_period',
        'report_xlsx',
        'date_range',
        'l10n_pe',
        'l10n_pe_extend',
        'l10n_pe_data',
        'l10n_pe_vat',
    ],
    'data': [
        'security/pe_account_security.xml',
        'security/ir.model.access.csv',
        'data/res_currency_data.xml',
        'wizard/pe_prepaid_wizard_view.xml',
        'views/account_view.xml',
        'views/account_move_view.xml',
        'views/product_view.xml',
        'views/currency_view.xml',
        'views/uom_view.xml',
        'views/pe_payment_date_view.xml',
        'views/users_view.xml',
        'views/pe_account_views.xml',
        'wizard/account_debit_note_view.xml',
        'wizard/account_move_reversal_view.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_pe_account/static/src/js/report/action_manager_report.esm.js",
        ],
    },
}