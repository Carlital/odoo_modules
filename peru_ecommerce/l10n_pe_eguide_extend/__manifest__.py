# -*- coding: utf-8 -*-
{
    'name': "Eguide Extend",

    'summary': """
        Electronic Guide""",

    'description': """
        Electronic Guide Advanced
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['l10n_pe_eguide'],

    'data': [
        'security/pe_eguide_security.xml',
        'security/ir.model.access.csv',
        'data/eguide_cron.xml',
        'views/pe_electronic_guide_views.xml',
        'views/pe_electronic_guide_session_views.xml',
        'views/pe_electronic_guide_branch_views.xml',
        'views/pe_electronic_guide_menus.xml',
        'report/report_electronic_guide_extend.xml'
    ],
}