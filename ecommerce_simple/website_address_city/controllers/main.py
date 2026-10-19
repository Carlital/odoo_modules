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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request
import logging
_log = logging.getLogger(__name__)


class CustomerPortalInherit(CustomerPortal):

    @http.route()
    def account(self, redirect=None, **post):
        country_id = post.get('country_id', '')
        state_id = post.get('state_id', '')
        if post.get('city_id'):
            post.update({'city_id':int(post.get('city_id'))})
        if country_id and state_id:
            country_id = request.env['res.country'].browse(int(country_id))
            if country_id.enforce_cities:
                cities = request.env['res.city'].search(
                    [('state_id', '=', int(state_id))])
                if cities:
                    self.MANDATORY_BILLING_FIELDS = [
                        "name", "phone", "email", "street", "city_id", "country_id"]
                    post.pop('city')
        else:
            self.MANDATORY_BILLING_FIELDS = [
                "name", "phone", "email", "street", "city", "country_id"]
        # country_id = request.env['res.country'].browse(int(country_id))
        res = super(CustomerPortalInherit, self).account(
            redirect=redirect, **post)
        return res


class WebsiteSaleInherit(WebsiteSale):
    @http.route()
    def address(self, **kw):
        request.session['state_id'] = kw.get('state_id', '')
        res = super(WebsiteSaleInherit, self).address(**kw)
        return res

    @http.route(['/shop/cities_infos'], type='json', auth="public", website=True)
    def cities_infos(self, state, country, **kw):
        zipcode = ''
        if country:
            country_id = request.env['res.country'].browse(int(country))
            if country_id.enforce_cities:
                cities = request.env['res.city'].search(
                    [('state_id', '=', int(state))])
                return {'cities': [(ct.id, ct.name,ct.zipcode) for ct in cities]}
        return {'result': False}

    @http.route(['/country/state/check'], type='json', auth="public", website=True)
    def state_infos(self, country, **kw):
        if country:
            country_id = request.env['res.country'].browse(int(country))
            if country_id.enforce_cities and country_id.state_ids:
                return {'result': min(country_id.state_ids).id}
        return {'result': False}

    def _get_mandatory_fields_shipping(self, country_id=False):
        res = super(WebsiteSaleInherit, self)._get_mandatory_fields_shipping(
            country_id=country_id)
        country_id = request.env['res.country'].browse(country_id)
        state_id = request.session.get('state_id', '')
        if country_id.enforce_cities and state_id:
            city_ids = request.env['res.city'].search(
                [('state_id', '=', int(state_id))])
            if city_ids:
                res.remove('city')
                res.append('city_id')

        return res

    def _get_mandatory_fields_billing(self, country_id=False):
        res = super(WebsiteSaleInherit, self)._get_mandatory_fields_shipping(
            country_id=country_id)
        country_id = request.env['res.country'].browse(country_id)
        state_id = request.session.get('state_id', '')
        if country_id.enforce_cities and state_id:
            city_ids = request.env['res.city'].search(
                [('state_id', '=', int(state_id))])
            if city_ids:
                res.remove('city')
                res.append('city_id')
        return res
