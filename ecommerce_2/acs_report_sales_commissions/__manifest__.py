{
    'name': 'Reporte de Comisiones de Ventas',
    'summary': 'Módulo para gestionar y reportar comisiones de ventas.',
    'description': """
        Este módulo extiende la funcionalidad de Odoo para permitir la gestión de comisiones de ventas.
        Incluye campos personalizados en las órdenes de venta y en los usuarios para definir
        porcentajes de comisión y vendedores comisionistas.
        También proporciona un resumen de comisiones por vendedor y orden de venta.""",
    'author': 'Juan Ayala (A&C Sistemas)',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Sales/Commissions',
    'version': '1.0',
    'depends': [
            'sale_management',  # Dependencia para el modelo sale.order
            'base',            # Dependencia para el modelo res.users
            'contacts',        # Dependencia para el modelo res.partner y menús
            'acs_sale_extra_calcs',  # Dependencia para el campo acs_type_exchange en sale.order
            'sale_crm',        # Dependencia para campos como opportunity_id y lost_reason_id
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_rubro_views.xml',  # Vista para gestionar rubros
        'views/res_partner_views.xml',        # Vista para añadir campo en contactos
        'views/res_users_views.xml',
        'views/res_company_views.xml',  # Vista para configurar comisión en compañía
        # Vista para mostrar campos de comisión en órdenes de venta
        'views/sale_order_views.xml',
        'views/commission_summary_views.xml',  # Vista del resumen de comisiones
        # Vista del reporte de ventas extendido
        'views/sale_extended_report_excel_wizard_views.xml',
        'views/sale_extended_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_report_sales_commissions/static/src/css/report_styles.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
