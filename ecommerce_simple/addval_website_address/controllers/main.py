# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request, route

_logger = logging.getLogger(__name__)


class WebsiteSaleAddressInfo(WebsiteSale):
    PHONE_PATTERN = re.compile(r'^(?:\+[0-9]{11}|[0-9]{11})$')

    def _get_country_related_render_values(self, kw, render_values):
        res = super()._get_country_related_render_values(kw, render_values)
        country_state_cities = request.env["res.city"].search([("code", "!=", False)])
        res.update({"country_state_cities": country_state_cities})
        # _logger.info("#################################")
        # _logger.info(res)
        # _logger.info(render_values)
        # _logger.info(render_values['checkout'])
        # _logger.info(type(render_values['checkout']))
        # _logger.info(render_values['checkout']['state_id'])
        # _logger.info(render_values['checkout'].id)
        return res

    def _get_mandatory_address_fields(self, country_sudo):
        fields = super()._get_mandatory_address_fields(country_sudo)
        fields.discard('zip')
        return fields

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            **kwargs,
        )

        phone = (address_values.get('phone') or '').strip()
        if phone and not self.PHONE_PATTERN.fullmatch(phone):
            invalid_fields.add('phone')
            error_messages.append(_("El teléfono debe tener 12 caracteres incluyendo '+' al inicio, o 11 números si no incluye '+'."))

        return invalid_fields, missing_fields, error_messages

    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super().checkout_form_validate(mode, all_form_values, data)

        phone = (all_form_values.get('phone') or '').strip()
        if phone and not self.PHONE_PATTERN.fullmatch(phone):
            error['phone'] = 'error'
            msg = _("Teléfono inválido. Debe tener 12 caracteres incluyendo '+' al inicio, o 11 números sin '+'. Vuelve a ingresarlo.")
            if msg not in error_message:
                error_message.append(msg)

        return error, error_message

    @http.route(
        [
            '/shop/state_infos/<model("res.country"):country>/<model("res.country.state"):state>'
        ],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, country, state, **kw):
        if country.id != state.country_id.id:
            return dict(in_country=False, use_selector=False, cities=[])
        cities = request.env["res.city"].search(
            [
                ("code", "!=", False),
                ("country_id", "=", country.id),
                ("state_id", "=", state.id),
            ]
        )
        use_selector = len(cities) > 0
        return dict(
            in_country=True,
            use_selector=use_selector,
            cities=cities.read(["id", "name"]),
        )


class PortalAddressInfo(CustomerPortal):
    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            
            if not error:
                # Procesar campos obligatorios y opcionales
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                
                # Convertir IDs de country_id y state_id a enteros
                for field in set(['country_id', 'state_id', 'city_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False

                # Actualizar el campo zip
                values.update({'zip': values.pop('zipcode', '')})
                
                # Llamada para procesar la actualización de la cuenta
                self.on_account_update(values, partner)
                
                # Escribir los valores actualizados en el partner
                partner.sudo().write(values)
                
                # Redirigir si es necesario
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        # Cargar países, estados y ciudades
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        cities = request.env["res.city"].sudo().search([("code", "!=", False)])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'partner_can_edit_vat': partner.can_edit_vat(),
            'redirect': redirect,
            'page_name': 'my_details',
            'cities': cities
        })
        _logger.info(partner.city_id)
        _logger.info(partner.city)

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
