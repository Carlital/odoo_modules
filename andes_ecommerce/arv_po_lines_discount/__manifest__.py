# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Lines Discount",
    'summary': """Apply discount as Amount ($)""",
    'description': """If you add a value by percentage it will automatically calculate the fixed amount for it, and vice versa in purchase order line.""",
    'author': "Aravind",
    'website': 'aravindu28@gmail.com',
    'version': '17.0.1.0',
    'sequence': 1,
    'license': "AGPL-3",
    'category': "Purchase Management",
    'depends': ['base', 'purchase'],
    'data': ['views/purchase_order.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/thumbnail.gif'],
}
