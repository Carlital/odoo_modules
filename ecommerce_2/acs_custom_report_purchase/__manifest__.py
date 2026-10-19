# -*- coding: utf-8 -*-
{
    'name': 'ACS Custom Purchase Report',  # <-- Nombre actualizado
    'version': '18.0.1.0.0',
    'summary': 'Customizes the Purchase Order PDF Report.',
    'description': """
        This module inherits the standard purchase order report to add custom modifications.
        Specifically, it modifies the shipping address block.
    """,
    'author': 'Juan Ayala',  # <-- Puedes poner el nombre de tu empresa
    'website': 'https://www.acsistemasperu.com',
    'category': 'Purchases',
    'depends': [
        'purchase',  # Dependencia clave
        #        'acs_signer_report_pdf',  # Asegura que este módulo se cargue después del de firma
    ],
    'data': [
        # Ruta al archivo XML que crearemos
        'views/purchase_order_report_templates.xml',
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
