{
    'name': 'Excel Sale Report',
    'version': '1.0',
    'description': 'Genera un reporte en Excel con productos y precios máximos, mínimos y medios.',
    'summary': 'Reporte en Excel para Ventas',
    'author': 'Carla Lomas',
    'license': 'LGPL-3',
    'depends': ['sale', 'base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_price_report_view.xml',
        'views/product_price_report_wizard_view.xml',
        'views/product_form_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/excel_sale_report/static/src/js/excel_export.js',
        ],
    },
}