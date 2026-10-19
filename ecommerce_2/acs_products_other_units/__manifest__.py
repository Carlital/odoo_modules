{
    'name': 'ACS Products Other Units',
    'version': '1.0',
    'summary': 'Add secondary units of measure to products',
    'description': """
        This module adds three fields to products:
        1. Secondary UoM - selector with UoM list
        2. Secondary Stock - float field for secondary stock value
        3. Conversion Ratio - calculated field (secondary stock / qty_available)
    """,
    'author': 'Juan Ayala',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Inventory',
    # Añadir 'sale_management'
    'depends': ['product', 'stock', 'sale_management'],
    'data': [
        'views/product_views.xml',
        'views/stock_quant_views.xml',
        'views/sale_views.xml',  # Añadir nueva vista
    ],
    'installable': True,
    'application': False,
}
