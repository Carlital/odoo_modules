{
    'name': 'WhatsApp CRM Integration',
    'version': '1.0',
    'category': 'CRM',
    'summary': 'Integrate WhatsApp with Odoo CRM',
    'depends': ['crm'],
    'data': [
        'views/whatsapp_crm_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': True,
}
