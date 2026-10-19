{
    'name': 'Edit Save Button In Odoo18',
    'version': '18.0.0.1',
    'summary': 'Edit Save Button Odoo18',
    'description': """
        This module introduces a streamlined way to manage records in Odoo 18 forms. 
        Users can easily switch between edit mode, save changes, or discard modifications 
        using intuitive buttons directly in the form view.
    """,
    'author': 'SPD Solutions',
    'company': 'SPD Solutions',
    'maintainer': 'SPD Solutions',
    'images': ['static/description/banner.png'],
    'depends': ['base'],
    'category': 'Tools',
    'assets': {
        'web.assets_backend': [
            '/spd_edit_save_button/static/src/views/form/form_controller.xml',
            '/spd_edit_save_button/static/src/views/form/form_controller.js',
        ]
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
