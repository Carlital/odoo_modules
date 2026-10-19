{
    'name': 'ACS Purchase Order Permissions',
    'version': '1.0',
    'summary': 'Adds a permission to prevent users from confirming purchase orders.',
    'author': 'Juan Ayala',
    'website': 'https://www.example.com',  # Reemplaza con tu website
    'license': 'LGPL-3',
    'depends': ['purchase'],
    'data': [
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
