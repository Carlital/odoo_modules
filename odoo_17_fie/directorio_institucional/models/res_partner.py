# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campo para identificar si es parte del directorio
    x_es_directorio = fields.Boolean(
        string='Es Directorio',
        compute='_compute_es_directorio',
        store=True,
        help='Indica si el contacto tiene la etiqueta "directorio"'
    )
    
    # Campos específicos del directorio institucional
    x_cargo_institucional = fields.Char(
        string='Cargo Institucional',
        help='Cargo o puesto que ocupa en la institución'
    )
    
    x_unidad_pertenece = fields.Char(
        string='Unidad a la que Pertenece',
        help='Departamento, facultad o unidad administrativa'
    )
    
    x_telefono_institucional = fields.Char(
        string='Teléfono Institucional',
        help='Número de teléfono institucional completo'
    )
    
    x_extension_telefonica = fields.Char(
        string='Extensión Telefónica',
        help='Extensión telefónica interna'
    )

    @api.depends('category_id')
    def _compute_es_directorio(self):
        """Computa si el contacto tiene la etiqueta 'directorio'"""
        for partner in self:
            partner.x_es_directorio = any(
                cat.name.lower() == 'directorio' 
                for cat in partner.category_id
            )

    @api.model
    def get_unidades_directorio(self):
        """Obtiene todas las unidades únicas del directorio"""
        directorio_tag = self.env['res.partner.category'].search([
            ('name', '=ilike', 'directorio')
        ], limit=1)
        
        if not directorio_tag:
            return []
        
        partners = self.search([
            ('category_id', 'in', [directorio_tag.id]),
            ('x_unidad_pertenece', '!=', False)
        ])
        
        unidades = partners.mapped('x_unidad_pertenece')
        # Eliminar duplicados y ordenar
        unidades_unicas = sorted(list(set(unidades)))
        
        return [{'id': unidad, 'name': unidad} for unidad in unidades_unicas]
