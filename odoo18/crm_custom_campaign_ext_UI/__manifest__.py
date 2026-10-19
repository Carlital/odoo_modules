{
    "name": "CRM Campaign Manager - UI Enhancement",
    "version": "1.0",
    "summary": "Interfaz visual mejorada para gestión de campañas comerciales",
    "description": """
        Módulo de extensión visual para crm_custom_campaign_ext.
        Proporciona:
        - Galería visual interactiva de planes
        - Drag & Drop para reordenar planes
        - Acciones rápidas en hover
        - Vista comercial mejorada
    """,
    "author": "C2Q",
    "license": "LGPL-3",
    "depends": [
        "crm_custom_campaign_ext",  # Módulo base con modelos y CRUD
        "web","crm_custom_lead"  # Para integración con crm.lead
    ],
    "data": [
        "views/bc_subcampaign_views_ui.xml",  # Hereda vistas para usar widgets
    ],
    "assets": {
        "web.assets_backend": [
            # JavaScript: Widgets OWL
            "crm_custom_campaign_ext_UI/static/src/js/bc_plan_gallery.js",
            "crm_custom_campaign_ext_UI/static/src/js/bc_subcampaign_gallery.js",
            
            # Templates XML
            "crm_custom_campaign_ext_UI/static/src/xml/bc_plan_gallery.xml",
            
            # Estilos CSS
            "crm_custom_campaign_ext_UI/static/src/css/bc_gallery.css",
        ]
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
