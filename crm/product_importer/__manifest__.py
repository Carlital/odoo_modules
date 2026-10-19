{
    'name': 'Product Importer',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Import products from an Excel template',
    'description': 'Module to import products from an Excel template',
    'depends': ['base', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_import_view.xml',
        'views/views_attributes.xml'
    ],
    'installable': True,
    'application': False,
}
