
{
    'name': 'Product Labels Price - ACS',
    'summary': '''Reporte etiquetas de precios''',
    'category': 'Product',
    'author': 'Anthony Gudiño <anthonygudino2@gmail.com>',
    'maintainer': 'Juan Ayala',
    'website': 'https://github.com/acsistemas',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'stock',
        'purchase',
        # 'acs_product_standard_name',
        # 'acs_product_view',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/product_report_price.xml',
        'report/product_report_barcode.xml',
        'wizard/tag_wizard_views.xml',
        'views/product_template_view.xml',
        'views/purchase_views.xml',
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
}
