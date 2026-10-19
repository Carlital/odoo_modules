# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

{
    'name' : 'Website Product Internal Reference(Default Code)',
    'category': 'Website',
    'version': '16.0.1.0',
    'author': 'Equick ERP',
    'description': """
        This Module allows to show product internal reference in webiste product page.
        * Customer can see the internal reference based on the product variant also.
        * Customer can able to view internal reference on grid and list view.
        * Support Multi Website.
    """,
    'summary': 'show product internal reference in webiste page display internal reference display default code show internal reference show default code website defualt code website internal reference variant default code variant internal reference website product sku',
    'depends' : ['base', 'website_sale'],
    'price': 15,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'views/website_sale_templates_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'eq_website_default_code/static/src/js/main.js',
        ],
    },
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
