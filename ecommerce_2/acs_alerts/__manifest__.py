{
    'name': "Acs Alerts",
    'summary': """
        Module to send alerts via pop up to users """,
    'author': "Daniel R.",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '18.0.0.1',
    'depends': ['base', 'bus', 'mail', 'point_of_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_alerts/static/src/js/service.js',
        ],
        'point_of_sale._assets_pos': [
            'acs_alerts/static/src/js/data_service.js',
        ],
    },
    'license': 'LGPL-3',
}