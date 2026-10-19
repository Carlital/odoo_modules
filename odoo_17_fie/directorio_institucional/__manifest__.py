# -*- coding: utf-8 -*-
{
    'name': 'Directorio Institucional',
    'version': '17.0.1.0.3',
    'category': 'Website',
    'summary': 'Directorio telefónico institucional para sitio web',
    'description': """
        Módulo para gestionar y mostrar el directorio telefónico institucional
        - Extiende res.partner con campos personalizados
        - Permite etiquetar contactos como "directorio"
        - Muestra snippet web con filtros por unidad
        - Incluye búsqueda por nombre
    """,
    'author': 'ESPOCH',
    'website': 'https://www.espoch.edu.ec',
    'depends': ['base', 'website', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/snippets_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'directorio_institucional/static/src/css/directorio.css',
            'directorio_institucional/static/src/js/directorio.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
