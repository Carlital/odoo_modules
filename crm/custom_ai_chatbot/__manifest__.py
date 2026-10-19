{
    'name': 'AI CRM Integration',
    'version': '1.0',
    'summary': 'Integración de IA con CRM en Odoo para Messenger y WhatsApp',
    'category': 'CRM',
    'author': 'Carla Lomas',
    'depends': ['crm', 'base', 'test_drive_management'],
    'data': [
        'views/faq_views.xml',
        'security/ir.model.access.csv',
        'data/faq_data.xml'
    ],
    'installable': True,
    'application': True,
}
