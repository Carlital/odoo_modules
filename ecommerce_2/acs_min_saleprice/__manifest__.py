# -*- coding: utf-8 -*-
{
    'name': 'ACS Precio Mínimo de Venta',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Aplica un precio de venta mínimo en los productos, considerando las reglas de las tarifas.',
    'author': 'Juan Ayala, acsistemasperu.com',
    'website': 'https://www.acsistemasperu.com',
    'license': 'AGPL-3',
    'depends': [
        'sale_management',  # Necesario para interactuar con Ventas
        'product',         # Necesario para interactuar con Productos
    ],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
