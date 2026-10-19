
{
    'name': 'Brand Comercial Tours - ACS',
    'author': 'Anthony Gudiño <anthonygudino2@gmail.com>, Daniel Robayo',
    'maintainer': 'Juan Ayala',
    'website': 'https://github.com/acsistemas',
    'category': 'CRM',
    'version': '17.0.0.1',
    'depends': [
        'account',
        'crm',
        'sale_crm',
        'sale_management',
        'mail',
        'point_of_sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/brand_security_groups.xml',
        'views/hotel_tour_views.xml',
        'views/brand_comercial_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_views.xml',
        'views/pos_config.xml',
        'views/account_invoice_views.xml',
        'report/sale_report_templates.xml',
        'data/mail_template.xml',
        'report/account_report_templates.xml',
        'views/res_users_views.xml',
        'views/stock_picking.xml',
        'report/stock_picking_report.xml',
        'data/email_template_marca.xml',
        
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'assets': {

        # Main PoS assets, they are loaded in the PoS UI and in the PoS unit tests
        'point_of_sale._assets_pos': [
            # PoS files
            'acs_brand_comercial/static/src/**/*',
        ],
      
    },
}
