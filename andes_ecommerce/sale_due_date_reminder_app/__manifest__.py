# -*- coding: utf-8 -*-
{
	'name': "Sale Due Date Reminder in Odoo",
	"author": "Edge Technologies",
	'version': "1.0",
	"live_test_url":'https://youtu.be/SJjo-bx5CTk',
	"images":["static/description/main_screenshot.png"],
	'summary': "Due date reminder on sales due date reminder to followers sale due date reminder to followers remind sale expiry date via email sales expiry date reminder to followers sales expiry date reminder sale expiry date reminder to sale order expiry date reminder",
	'description': """						
       App for remind sale due date via email to all sales followers. this apps helps to remind sale due date via email to all sales followers.
       Sales due date reminder to followers in odoo.sales order due date reminder to all followers in odoo. sale due date reminder to followers in odoo.sale order due date reminder to all followers in odoo.sale reminder sale order reminder on sales order based on due date
       Due date reminder on sales order in odoo. expiry date reminder on sales order on odoo.
App for remind sale expiry date via email to all sales followers. sale expiry date via email to all sales followers.
       Sales expiry date reminder to followers in odoo.sales order expiry date reminder to all followers in odoo. sale expiry date reminder to followers in odoo.sale order expiry date reminder to all followers in odoo. 

					""",
    "license" : "OPL-1",
    'depends': ['base', 'sale_management'],
	'data': [
			'data/sale_due_remainder_email.xml',
			'data/sale_due_remainder_sheduler.xml',
			'views/sale_due_remainder_view.xml',
			],
	'installable': True,
	'auto_install': False,
	'application': False,
	'category': " Sales",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
