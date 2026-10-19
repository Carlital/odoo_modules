# -*- coding: utf-8 -*-
{
    'name': "Peruvian Electronic Voucher From",

    'summary': """
        cpe, website""",

    'description': """
        CPE form for search invoices
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Website',
    'version': '0.1',

    'depends': [
        'website',
        # 'l10n_pe_cpe'
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/pe_query_cpe_form_data.xml',
        'data/website_data.xml',
        'data/pe_query_cpe_form_data.xml',
        #'views/snippets/s_website_form.xml',
        'views/account_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'l10n_pe_cpe_form/static/src/snippets/s_website_form/000.js',
        ],
    },
}
