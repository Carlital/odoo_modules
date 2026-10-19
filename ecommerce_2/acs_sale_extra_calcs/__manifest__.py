{
    'name': 'ACS Sale Extra Calculations',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Campos adicionales y cálculos para ventas',
    'description': """
        Añade campos personalizados en líneas de venta y cabecera de pedidos
        con cálculos automáticos de piezas, metros y conversión monetaria.
    """,
    'author': 'Juan Ayala',
    'website': 'https://www.acsistemasperu.com',
    'depends': ['base', 'sale', 'sale_management', 'web', 'account', 'hr', 'acs_signer_report_pdf'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/sale_order_line_colors_views.xml',
        'views/product_template_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_manufacturing_views.xml',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
        'views/report_saleorder_document_inherit.xml',
        'report/sale_order_manufacturing_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_sale_extra_calcs/static/src/css/manufacturing_styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
