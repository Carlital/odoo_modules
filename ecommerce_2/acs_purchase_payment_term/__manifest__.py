
{
    'name': 'Purchase Payment Term - ACS',
    'summary': '''''',
    'category': 'Purchase',
    'version': '18.0.0.1',
    'author': 'Anthony Gudiño <anthonygudino2@gmail.com>',
    'maintainer': 'Juan Ayala',
    'website': 'https://github.com/acsistemas',
    'license': 'AGPL-3',
    'depends': [
        'purchase','stock','l10n_latam_invoice_document'
    ],
    'data': [
        'views/account_views.xml',
        'views/purchase_views.xml',
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
}
