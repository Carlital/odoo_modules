{
    'name': 'ACS Sale Report Option 1',
    'version': '1.0',
    'summary': 'Agrega columnas personalizadas al reporte de sale.order',
    'category': 'Sales',
    'author': 'Juan Ayala',
    'depends': ['sale'],
    'data': [
        'views/report_saleorder_document_inherit.xml',
    ],
    'installable': True,
    'application': False,
}