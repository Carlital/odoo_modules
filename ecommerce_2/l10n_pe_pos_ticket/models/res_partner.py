# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _load_pos_data_fields(self, config_id):
        """
        Añade los campos de dirección peruanos a la carga del POS
        """
        fields = super()._load_pos_data_fields(config_id)

        # Campos adicionales necesarios
        additional_fields = [
            'l10n_pe_district',
            'city_id',
            'state_id',
        ]

        # Agregar campos sin duplicados
        for field in additional_fields:
            if field not in fields:
                fields.append(field)

        return fields

    def _load_pos_data(self, data):
        """
        Procesa los datos de partners para convertir Many2one al formato [id, nombre]
        """
        # Llamar al método padre para obtener los partners
        partners = super()._load_pos_data(data)

        # Procesar cada partner para convertir Many2one a formato [id, nombre]
        for partner in partners:
            # Convertir city_id de int a [id, nombre]
            if partner.get('city_id') and isinstance(partner['city_id'], int):
                city = self.env['res.city'].browse(partner['city_id'])
                partner['city_id'] = [
                    city.id, city.name] if city.exists() else False

            # Convertir state_id de int a [id, nombre]
            if partner.get('state_id') and isinstance(partner['state_id'], int):
                state = self.env['res.country.state'].browse(
                    partner['state_id'])
                partner['state_id'] = [
                    state.id, state.name] if state.exists() else False

            # Convertir country_id de int a [id, nombre] (por si acaso)
            if partner.get('country_id') and isinstance(partner['country_id'], int):
                country = self.env['res.country'].browse(partner['country_id'])
                partner['country_id'] = [country.id,
                                         country.name] if country.exists() else False

            # Manejar l10n_pe_district (puede ser Many2one o Char)
            if partner.get('l10n_pe_district'):
                # Verificar si es entero (Many2one)
                if isinstance(partner['l10n_pe_district'], int):
                    try:
                        district = self.env['l10n_pe.res.city.district'].browse(
                            partner['l10n_pe_district'])
                        partner['l10n_pe_district'] = [district.id,
                                                       district.name] if district.exists() else False
                    except KeyError:
                        _logger.warning(
                            "No se pudo convertir l10n_pe_district. "
                            "El modelo 'l10n_pe.res.city.district' no existe."
                        )
                        partner['l10n_pe_district'] = False

                # Si es string (campo Char), convertir a formato [False, string]
                elif isinstance(partner['l10n_pe_district'], str):
                    partner['l10n_pe_district'] = [
                        False, partner['l10n_pe_district']]

        return partners
