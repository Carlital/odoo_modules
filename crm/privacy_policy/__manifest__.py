{
    'name': 'Privacy Policy',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Privacy Policy Page',
    'depends': ['base', 'website'],
    'data': [
        'views/privacy_policy_template.xml',
        'views/privacy_policy_views.xml',  # Solo si utilizas el modelo opcional
    ],
    'application': True,
    'installable': True,
}
