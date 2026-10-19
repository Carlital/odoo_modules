# acs_archive_pos_orders/__manifest__.py
{
    'name': "ACS Archive POS Orders",
    'summary': "Módulo para archivar masivamente órdenes de POS desde un wizard",
    'description': """
        Este módulo permite archivar todas las órdenes de POS mediante un wizard con un botón.
        Al finalizar, muestra un mensaje de "Tarea completada".
    """,
    'author': "Tu Nombre",
    'version': '18.0.1.0.0',
    'depends': ['point_of_sale', 'base'],  # 'base' para el menú en Ajustes
    'data': [
        'security/ir.model.access.csv',
        'views/mass_archive_wizard_views.xml',
        'views/pos_order_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}