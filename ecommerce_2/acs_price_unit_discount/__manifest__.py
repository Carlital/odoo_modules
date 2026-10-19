{
    'name': 'ACS Precio Unitario con Descuento',
    'version': '18.0.1.0.0',
    'summary': 'Añade una columna para el precio unitario con descuento en líneas de venta y facturas',
    'description': """
        Este módulo agrega un campo calculado 'Precio unitario con descuento' 
        en las líneas de pedidos de venta, facturas y notas de crédito, 
        mostrando el precio unitario tras aplicar el descuento.
    """,
    'author': 'Juan Ayala - AC Sistemas Perú',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Sales',
    'depends': ['sale', 'account'],
    'data': [
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}