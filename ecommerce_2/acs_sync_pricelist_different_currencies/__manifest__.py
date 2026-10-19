{
    'name': 'ACS Sync Pricelist Different Currencies',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Sincroniza listas de precios con diferentes monedas',
    'description': '''
        Este módulo permite sincronizar dos listas de precios con diferentes monedas,
        manteniendo los precios actualizados según el tipo de cambio.
        
        Características principales:
        - Sincronización automática de productos entre listas de precios
        - Actualización automática de precios basada en el tipo de cambio
        - Soporte para variantes de productos
        - Actualización automática cuando cambia el tipo de cambio
    ''',
    'author': 'Juan Ayala',
    'company': 'A&C Sistemas',
    'website': 'https://www.acsistemasperu.com',
    'depends': [
        'base',
        'product',
        'sale_management',
    ],
    'data': [
        'views/product_pricelist_views.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
