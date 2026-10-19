# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
{
    "name":  "Odoo Website Address City",
    "summary":  """Odoo Website Address City modifies the Odoo base_ address_city module and makes it more convenient for the user to add their address on the Odoo website.
                    Further, the Odoo admin can add the city address in the backend which users can select from the website. Admin can add website city groups means they can add the cities in different states, UTs, or counties.
                    """,
    "category":  "eCommerce",
    "version":  "1.0.0",
    "license":  "Other proprietary",
    "sequence":  1,
    'application': True,
    "website": "https://store.webkul.com/",
    "author":  "Webkul Software Pvt. Ltd.",
    "description":  """Odoo Website Address City allows you to create cities in Odoo so your customer can fill their address more efficiently.
                    """,
    "live_test_url":  "http://odoodemo.webkul.com/?module=website_address_city",
    "depends":  [
        'base_address_extended', 'website_sale','contacts'],
    'data': [
        'data/data.xml',
        'views/country_views.xml',
        'views/templates.xml'],
    'assets': {
        'web.assets_frontend': [
            'website_address_city/static/src/js/website_sale.js',
            'website_address_city/static/src/js/portal.js',
        ],
    },
    "images":  ['static/description/odoo-website-address-city-v15.gif'],
    "installable":  True,
    "auto_install":  False,
    "price":  25,
    "currency":  "USD",
    "pre_init_hook": "pre_init_check",
}
