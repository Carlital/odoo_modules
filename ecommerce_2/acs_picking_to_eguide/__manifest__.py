{
    'name': 'ACS Picking to Eguide',
    'version': '1.0',
    'summary': 'Conecta stock picking con guías electrónicas (pe.electronic.guide)',
    'description': 'Modulo para autocompletar guías electrónicas desde picking validados y añadir botón Crear Guia.',
    'author': 'Juan Ayala - A&C Sistemas',
    'category': 'Inventory',
    'depends': ['base', 'stock', 'l10n_pe_eguide', 'l10n_pe_eguide_advanced'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
