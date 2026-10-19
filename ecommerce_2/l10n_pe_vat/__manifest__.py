# -*- coding: utf-8 -*-
{
    'name': "Peruvian docs validators",

    'summary': """
        Validate RUC and DNI
        """,

    'description': """
    Este addon valida el ruc de los clientes con la SUNAT
    """,

    'author': "Grupo YACCK",
    'website': "www.grupoyacck.com",

    'category': 'Localization/Peruvian',
    'version': '18.0.0.1',

    'depends': [
        'base',
        'l10n_pe',
        'l10n_latam_base'
    ],

    'data': [
        'views/res_partner_view.xml',
    ],
}
