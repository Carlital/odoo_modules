# -*- coding: utf-8 -*-
{
    'name': 'ACS Product Supplier Info',
    'version': '18.0.1.0.0',
    'summary': 'Añade un menú para visualizar la información de proveedores por producto.',
    'description': """
        Este módulo extiende la funcionalidad de Odoo para añadir un acceso directo
        en el menú de Inventario que muestra una lista con la información de los
        proveedores (product.supplierinfo).
    """,
    'author': 'Juan Ayala - ACS Sistemas Peru',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Inventory/Purchase',
    'license': 'AGPL-3',
    'depends': [
        'purchase_stock',  # Dependencia que incluye 'purchase' y 'stock'
        'product',
        'mail',
    ],
    'data': [
        'views/product_supplierinfo_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
