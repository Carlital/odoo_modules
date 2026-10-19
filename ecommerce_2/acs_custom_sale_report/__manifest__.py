{
    'name': 'Custom Sale Report for Quotations/Orders',
    'version': '18.0.1.0.0',
    'summary': 'Custom PDF report for sales quotations and orders',
    'description': 'This module adds a custom PDF report for sales quotations and orders in Odoo 17, mimicking the provided design.',
    'category': 'Sales',
    'author': 'Juan Ayala',
    'depends': ['sale_management', 'base'],
    'data': [
        'data/report_paperformat.xml',
        'report/sale_report_templates.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}