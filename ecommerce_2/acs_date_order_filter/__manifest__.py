# -*- coding: utf-8 -*-
{
    'name': 'ACS Sale Order Date Filter',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Adds a date-only field from date_order for filtering purposes.',
    'description': """
        This module adds a new field 'date_order_filter' of type Date to the
        sale.order model. This field automatically stores the date part of the
        'date_order' (DateTime) field, making it easier to filter and group
        sales orders by date. The field is computed and stored for performance.
    """,
    'author': 'Juan Ayala (Smartech)',
    'website': 'https://www.smartech.pe',
    'depends': [
        'sale_management',
    ],
    'data': [
        'views/sale_order_view.xml',
        'views/sale_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
