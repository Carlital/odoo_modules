{
    'name': 'ACS Custom Report Delivery',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Personalización del reporte de entrega/picking',
    'description': """
        Módulo para personalizar el reporte de entrega de Odoo.
        - Elimina header y footer
        - Diseño personalizado similar a formato de ticket
    """,
    'author': 'Juan Ayala - A&C Sistemas',
    'website': 'https://www.acsistemasperu.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'data/paperformat_data.xml',
        'reports/report_delivery_custom.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
