
{
    'name': 'ACS POS Show price',
    'summary': '''añadir precios a la tarjetas del pos''',
    'category': 'Point of Sale',
    'author': 'Cristhian G.',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale'
    ],
    'data': [
        

    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'acs_pos_show_price/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
