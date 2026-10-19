{
    "name": "CRM Custom Lead",
    "version": "1.0.2",
    "summary": "Extension de crm.lead con validaciones personalizadas",
    "author": "C2Q",
    "license": "LGPL-3",
    "depends": ["crm", "hr", "base_address_extended", "web"],
    "data": [
        "data/groups.xml",
        "data/stages.xml",
        "data/sequence.xml",
        "data/hr_employee_motorizado_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/crm_campaign_views.xml",
        "views/res_parish_views.xml",
        "views/hr_employee_motorizado_views.xml",
        "views/crm_lead_views.xml",
        "views/menu_overrides.xml",
        "views/web_layout_override.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # CSS
            "crm_custom_lead/static/src/css/chip_selector.css",
            "crm_custom_lead/static/src/css/card_input_mask.css",
            "crm_custom_lead/static/src/css/form_styles.css",
            # JS
            "crm_custom_lead/static/src/js/chip_selector_widget.js",
            "crm_custom_lead/static/src/js/card_input_mask.js",
            # XML
            "crm_custom_lead/static/src/xml/chip_selector_template.xml",
            "crm_custom_lead/static/src/xml/card_input_mask.xml",
        ],
    },
    "application": True,
}