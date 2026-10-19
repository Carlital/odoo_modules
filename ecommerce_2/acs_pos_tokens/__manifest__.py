
{
    'name': 'ACS POS Tokens',
    'summary': '''Reporte etiquetas de precios''',
    'category': 'Point of Sale',
    'author': 'Cristhian G.',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale'
    ],
    'data': [
        'security/pos_token_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/pos_token_views.xml',
        'views/pos_token_menu.xml',

    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'acs_pos_tokens/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
