{
    'name': 'Preserve Discount in Sales Lines',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Maintains the discount percentage when changing quantity in sales order lines',
    'description': """
        This module modifies the standard Odoo behavior to maintain
        the discount percentage when changing the quantity in sales order lines.
        
        Features:
        - Preserves manual discount when changing quantity
        - Recalculates total price based on existing discount
    """,
    'author': 'Dustin Mimbela',
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
