{
    'name': 'Izipay Recargos',
    'version': '1.0',
    'category': 'Payment',
    'summary': 'Gestión de recargos para IziPay',
    'author': 'Carla Lomas',
    'depends': ['payment', 'website_sale', 'payment_micuentaweb', 'sale'],
    'data': [
        'views/payment_acquirer_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'acs_izipay_extra_fees/static/src/js/payment_extra_fee.js',
        ],
    },
    'installable': True,
    'application': False,
}
