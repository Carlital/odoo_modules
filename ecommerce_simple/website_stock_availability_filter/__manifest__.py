# -*- coding: utf-8 -*-
# Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details
{
    'name': 'Website Stock Availability Filter',
    'summary': """Display Products Avaliable in Stock On Website.""",
    'version': '16.0.0.1',
    'author': 'Bizople Solutions Pvt. Ltd',
    'website': "https://www.bizople.com/",
    'category': "Website",
    'description': """Display Products Avaliable in Stock On Shop Page and Category Page.""",
    "depends": [
        'website_sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_page_template.xml',
    ],
    'assets':{
        'web.assets_frontend' : [
            "/website_stock_availability_filter/static/src/scss/product_label.scss",
        ],
    },
    'images': [
        'static/description/banner.png'
    ],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install':False,
    'price': 30,
    'license': 'OPL-1',
    'currency': 'EUR',
}
