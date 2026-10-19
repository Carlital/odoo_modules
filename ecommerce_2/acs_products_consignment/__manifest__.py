{
    'name': 'Product Consignment',
    'version': '1.0',
    'summary': 'Manage consignment clients for products',
    'description': 'Adds a consignment client field to products and a custom filter in stock view',
    'author': 'Juan Ayala',
    'depends': ['base', 'product', 'stock'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_views.xml',
    ],
    'installable': True,
    'application': True,
}
