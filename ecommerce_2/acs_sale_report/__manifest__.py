{
    'name': 'ACS Sale Report',
    'version': '18.0.1.0.0',
    'summary': 'Personalización del diseño de cotizaciones en Odoo',
    'author': 'Juan Ayala - ACSistemasPeru',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Sales',
    'depends': ['base','sale','acs_price_unit_discount'],
    'data': [
        'views/report_saleorder_document.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
}