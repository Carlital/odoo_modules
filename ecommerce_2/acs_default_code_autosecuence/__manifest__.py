{
    'name': 'ACS Default Code Autosequence',
    'version': '18.0.1.0.0',
    'summary': 'Automatically generates a sequence for the internal reference on products.',
    'author': 'ACSistemas',
    'company': 'ACSistemas',
    'maintainer': 'ACSistemas',
    'website': 'https://www.acsistemas.com',
    'category': 'Inventory/Purchase',
    'depends': ['product', 'acs_advanced_search'],
    'data': [
        'data/ir_sequence_data.xml',
        #        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
