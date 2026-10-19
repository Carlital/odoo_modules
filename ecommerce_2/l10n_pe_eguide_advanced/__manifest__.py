# -*- coding: utf-8 -*-
{
    'name': "Eguide Advanced",

    'summary': """
        Electronic Guide""",

    'description': """
        Electronic Guide Advanced
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'stock',
        'fleet',
        'base_address_extended',
        'l10n_pe',
        'l10n_pe_data',
        'l10n_pe_vat',
        'l10n_pe_account',
        'l10n_pe_extend',
    ],

    'data': [
        'security/pe_eguide_security.xml',
        'wizard/pe_eguide_advanced_import_view.xml',
        'report/electronic_guide_custom_template.xml',
        'report/electronic_guide_standard_template.xml',
        'report/electronic_guide_stylized_template.xml',
        'report/report_electronic_guide_extend.xml',
        'security/ir.model.access.csv',
        'data/eguide_cron.xml',
        'views/pe_electronic_guide_views.xml',
        'views/pe_electronic_guide_session_views.xml',
        'views/pe_electronic_guide_branch_views.xml',
        'views/res_config_settings_views.xml',
        'views/pe_electronic_guide_menus.xml',
        'wizard/pe_eguide_advanced_wizard_view.xml',
        'views/stock_picking_views.xml',
    ],
}