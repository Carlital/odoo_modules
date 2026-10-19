{
    'name': 'ACS Invoice Blocker',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Bloquea el cambio de estado a borrador en facturas CPE publicadas',
    'description': '''
        Este módulo impide que las facturas que son CPE (Comprobante de Pago Electrónico)
        y están en estado publicado (posted) sean cambiadas a estado borrador (draft).
    ''',
    'author': 'Juan Ayala',
    'company': 'A&C Sistema',
    'website': 'https://www.acsistemasperu.com',
    'depends': [
        'account',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
