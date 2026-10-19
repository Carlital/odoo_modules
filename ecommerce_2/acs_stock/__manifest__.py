
{
    'name': 'Stock- ACS',
    'category': 'Stock',
    "version": "18.0.0.1",
    'author': 'Anthony Gudiño <anthonygudino2@gmail.com>',
    'maintainer': 'Juan Ayala',
    'website': 'https://github.com/acsistemas',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'account',
        'sale_stock',
        'purchase',
    ],
    'data': [
        'views/stock_picking_views.xml',
        'security/security.xml',
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
}
