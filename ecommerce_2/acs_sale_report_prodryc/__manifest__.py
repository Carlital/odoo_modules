{
    'name': 'ACS Sale Report Prodryc',
    'version': '18.0.1.0.0',
    'summary': 'Personalización del diseño de cotizaciones en Odoo para Prodryc',
    'author': 'Juan Ayala - ACSistemasPeru',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Sales',
    'depends': ['base','sale','acs_price_unit_discount'],
    'data': [
        'views/report_saleorder_document.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "acs_sale_report_prodryc/static/src/*",            
            ],
    },
    'application': False,
}