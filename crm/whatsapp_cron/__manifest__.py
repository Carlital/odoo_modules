{
    'name': 'WhatsApp CRM',
    'version': '1.0',
    'category': 'Sales',
    'license': 'LGPL-3',
    'summary': 'Send WhatsApp messages and manage CRM opportunities',
    'description': 'A module to send WhatsApp messages and manage CRM opportunities',
    'author': 'Carla Lomas',
    'depends': ['base', 'crm'],
    'data': [
        'data/whatsapp_cron.xml',
    ],
    'installable': True,
    'application': True,
}