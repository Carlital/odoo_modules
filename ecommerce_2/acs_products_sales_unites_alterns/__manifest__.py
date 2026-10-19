{
    'name': 'ACS Products Sales Units Alterns',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Conversión automática de productos de peso a metros lineales',
    'description': """
        Módulo para convertir automáticamente productos comprados en unidades de peso
        (kg, toneladas) a unidades de longitud (metros lineales) mediante pickings
        automáticos que respetan los flujos nativos de Odoo.
        
        Características:
        - Configuración de productos con ratios de conversión peso/longitud
        - Botón de conversión en pickings de recepción
        - Generación automática de pickings de salida y recepción
        - Mantenimiento de trazabilidad completa
    """,
    'author': 'Juan Ayala',
    'website': 'https://www.acsistemasperu.com',
    'depends': ['stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/res_users_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
