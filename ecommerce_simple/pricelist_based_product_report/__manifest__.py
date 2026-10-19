# -*- coding: utf-8 -*-

{
    'name': 'Pricelist Based Product Report',
    'version': '1.20210719',
    'category': 'Report',
    'summary': "Allows you to print pricelist based report for products from website" ,
    'description': "Allows you to print pricelist based report for products from website",
    'depends': ['portal','product','stock','website_sale','product_manufacturer','website_product_brands'],
    'data': [
        'views/report_view.xml',
        'views/views.xml',
        'wizard/pricelist_based_product_report_wizard_view.xml',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
}
