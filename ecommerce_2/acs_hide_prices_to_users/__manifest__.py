{
    'name': 'Hide Prices for Users',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Hide product prices for specific users',
    'description': """
        This module adds the ability to hide product prices for specific users.
        It adds a boolean field in user preferences to control price visibility.
    """,
    'author': 'Juan Ayala',
    'company': 'A&C Sistemas',
    'website': 'http://www.acsistemasperu.com',
    'depends': ['base', 'stock', 'product'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
