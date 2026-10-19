# -*- encoding: utf-8 -*-

{
    "name": "Pdf Print Preview",
    "version": "18.1.4",
    "depends": ["web"],
    "author": "itechgroup",
    "category": "web",
    "website": "",
    "summary": """Preview and print PDF report in your browser | Pdf direct preview | Print without Download
    | Quick printer | Easily to print report | Without download PDF File | Preview without Download | Preview report
    | Preview pdf | Odoo direct print | pdf preview | report Preview | PDF Viewer | report Viewer | PDF
    """,
    "description": """
        Preview,
        Preview PDF,
        Preview print PDF,
        Preview report,
        Report,
        Print,
        Pdf direct preview,
        PDF preview,
        Direct preview,
        Direct print,
        Print Without Download,
        Print without,
        Download,
        Without Download,
        Quick Printer,
        Printer,
        Quick Pdf,
        Pos report,
        Pos,
        Sale,
        Purchase,
        Stock,
        Print report,
        Easily to print report,
        Without download PDF File,
        Preview without Download
    """,
    "live_test_url": "https://www.itechgroup.info/demo-request?utm_source=odoo-apps&utm_medium=demo-request&utm_campaign=pdf-preview-17",
    "support": "support@itechgroup.info",
    'website': "https://www.itechgroup.info/",
    "data": [
        "views/res_users.xml",
        "report/ir_actions_report_templates.xml",
        "report/ir_actions_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pdf_print_preview/static/src/js/pdf_preview.js",
            "pdf_print_preview/static/src/js/user_menu.js",
            "pdf_print_preview/static/src/xml/pdf_viewer_dialog.xml"
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "license": "OPL-1",
    "currency": "EUR",
    "price": 25.99
}
