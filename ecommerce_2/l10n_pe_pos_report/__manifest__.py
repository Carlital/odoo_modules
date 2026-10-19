# -*- coding: utf-8 -*-
{
    'name': "Pos Report",

    'summary': """
        Pos Report""",

    'description': """
        Pos Report
    """,

    'author': "Grupo YACCK",
    'website': "http://www.grupoyacck.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['l10n_pe_pos_cpe'],

    'data': [
        # 'security/ir.model.access.csv',
        "report/detailed_sales_report_view.xml",
        "report/box_closure_report_view.xml",
        "views/pos_report.xml",
    ],
}
