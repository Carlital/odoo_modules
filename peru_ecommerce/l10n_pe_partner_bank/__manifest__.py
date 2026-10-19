# -*- coding: utf-8 -*-
{
    'name': "Peruvian Banks Data",

    'summary': """
        Add Account Type
        Add Number CCI
        Add No Print Report
        """,

    'description': """
    Este addons Aumenta Datos Necesarios de Bancos en Peru
    """,

    'author': "DISOTEC, Grupo YACCK",
    'website': "http://disotecperu.com",
    'license': 'AGPL-3',
    'category': 'Localization/Peruvian',
    'version': '17.0.0.1',

    'depends': [
        'base',
        'l10n_pe_cpe',
    ],
    'data': [
        'views/res_partner_bank_view.xml',
        'views/cpe_report_invoice.xml',
    ],
}
