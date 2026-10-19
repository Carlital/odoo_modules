{
    'name': 'Barcode Quantity Popup',
    'version': '1.0',
    'summary': 'Popup para configurar cantidad al agregar productos por código de barras.',
    'author': 'Carla Lomas',
    'license': 'LGPL-3',
    'category': 'Point of Sale',
    'depends': [
        'base', 'web','point_of_sale'
    ],
    'data': [
        'views/templates.xml',
    ],
    'auto_install': False,
    'application': False,
    'assets': {
        'point_of_sale.assets': [
            '/barcode_quantity_popup/static/src/css/popup_quantity.css',
            '/barcode_quantity_popup/static/src/js/popup_quantity.js',
        ],
    }
}