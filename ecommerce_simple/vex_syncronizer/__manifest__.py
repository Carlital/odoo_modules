{
    'name': 'Synchronizer Vex',
    'version': '1.0',
    'description': 'Module to synchronize data between Vex and other platforms',
    'summary': 'Data synchronization for Vex',
    'author': 'Vex Soluciones',
    'contributors': [
        'Luis Enrique Alva Villena'
        ],
    'website': 'https://www.yourwebsite.com',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base',
        'product',
        'sale',
        'contacts',

    ],
    'data': [
        'security/security.xml',
        'menus/menu.xml',
        'views/vex_instance.xml',
        'views/vex_product_template.xml',
        'views/vex_sale_order.xml',
        'views/vex_product_category.xml',
        'views/vex_res_partner.xml',
    ],
    'demo': [],
    'auto_install': False,
    'application': False,
    'assets': {
    }
}