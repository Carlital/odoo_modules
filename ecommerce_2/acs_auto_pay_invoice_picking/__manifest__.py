{
    'name': 'ACS Invoice and Picking Automation',
    'version': '1.0',
    'summary': 'Automates invoicing and picking from sales orders',
    'author': 'Juan Ayala',
    'depends': ['sale', 'stock', 'account', 'l10n_pe_cpe', 'l10n_pe_sale', 'l10n_latam_base','base_fontawesome'],  # Dependencias necesarias
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/account_journal_views.xml',
        'views/account_payment_term_views.xml',
        'views/account_move_views.xml',
        'reports/sale_order_ticket_report.xml',
        'reports/account_move_ticket_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
