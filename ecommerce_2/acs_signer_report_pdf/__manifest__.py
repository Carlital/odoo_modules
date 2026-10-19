# -*- coding: utf-8 -*-
{
    'name': 'Firma de Usuario en Imagen',
    'version': '18.0.1.0.0',
    'summary': 'Permite a los usuarios subir una imagen de su firma en su perfil.',
    'description': """
        Este módulo agrega un campo de tipo imagen en el perfil del usuario
        para que puedan cargar una foto de su firma manuscrita.
    """,
    'author': 'Juan Ayala, www.acsistemasperu.com',
    'website': 'https://www.acsistemasperu.com',
    'category': 'Human Resources/Employees',
    'depends': ['hr', 'purchase'],
    'data': [
        'views/res_users_view.xml',
        'views/purchase_order_view.xml',
        'views/purchase_report_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
