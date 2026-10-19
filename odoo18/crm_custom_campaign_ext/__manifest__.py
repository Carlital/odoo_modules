{
    "name": "CRM Custom Campaign Manager",
    "version": "1.0",
    "summary": "Extiende campañas: subcampañas y planes con atributos dinámicos",
    "author": "C2Q",
    "license": "LGPL-3",
    "depends": ["base","crm_custom_lead", "web","crm"],
    "data": [
        'data/campaign_init.xml',
        'data/plan_base_template.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        "views/n8n_config_wizard_views.xml",
        "wizards/plan_import_views.xml",
        "wizards/gsheet_import_views.xml",
        "views/bc_campaign_views.xml",
        "views/bc_subcampaign_views.xml",
        "views/bc_plan_views.xml",
        "views/crm_lead_bc_views.xml",
        "views/bc_icon_views.xml",
        "views/bc_campaign_id.xml",

    ],
    "application": True,
    'post_init_hook': 'post_init_hook',
}

