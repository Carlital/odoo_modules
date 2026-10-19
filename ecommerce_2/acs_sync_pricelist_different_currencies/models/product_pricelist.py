from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.model_create_multi
    def create(self, vals_list):
        items = super().create(vals_list)
        for item in items:
            if item.pricelist_id.is_source_pricelist and item.pricelist_id.target_pricelist_id:
                item.pricelist_id._sync_item_to_target(item)
        return items

    def write(self, vals):
        result = super().write(vals)
        if 'fixed_price' in vals:
            for item in self:
                if item.pricelist_id.is_source_pricelist and item.pricelist_id.target_pricelist_id:
                    item.pricelist_id._sync_item_to_target(item)
        return result


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_source_pricelist = fields.Boolean(
        string='Es Lista de Precios Fuente',
        help='Marque esta opción si esta es la lista de precios principal (USD)'
    )
    target_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios Destino',
        help='Lista de precios que se actualizará automáticamente (PEN)'
    )
    source_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Lista de Precios Fuente',
        compute='_compute_source_pricelist',
        store=True,
        help='Lista de precios fuente que controla esta lista'
    )

    @api.depends_context('force_recompute')
    @api.depends('target_pricelist_id', 'is_source_pricelist')
    def _compute_source_pricelist(self):
        for record in self:
            source = self.search([
                ('is_source_pricelist', '=', True),
                ('target_pricelist_id', '=', record.id)
            ], limit=1)
            record.source_pricelist_id = source.id if source else False

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get('target_pricelist_id'):
            target = self.browse(vals['target_pricelist_id'])
            target.invalidate_recordset(['source_pricelist_id'])
            target._compute_source_pricelist()
        return res

    def write(self, vals):
        old_targets = self.mapped('target_pricelist_id')
        res = super().write(vals)
        if 'target_pricelist_id' in vals or 'is_source_pricelist' in vals:
            # Recalcular source_pricelist_id en las listas destino anteriores
            if old_targets:
                old_targets.invalidate_recordset(['source_pricelist_id'])
                old_targets._compute_source_pricelist()
            # Recalcular source_pricelist_id en las nuevas listas destino
            if 'target_pricelist_id' in vals:
                new_targets = self.filtered(
                    'target_pricelist_id').mapped('target_pricelist_id')
                new_targets.invalidate_recordset(['source_pricelist_id'])
                new_targets._compute_source_pricelist()
        return res

    def write(self, vals):
        result = super().write(vals)
        if 'target_pricelist_id' in vals:
            for record in self:
                if record.is_source_pricelist and record.target_pricelist_id:
                    record._update_all_target_items()
        return result

    @api.constrains('is_source_pricelist', 'currency_id', 'target_pricelist_id')
    def _check_currency_and_target(self):
        for record in self:
            if record.is_source_pricelist and record.target_pricelist_id:
                if record.currency_id == record.target_pricelist_id.currency_id:
                    raise UserError(
                        'La lista de precios fuente y destino deben tener '
                        'diferentes monedas.'
                    )

    def action_sync_prices(self):
        """Acción para sincronizar manualmente los precios"""
        self.ensure_one()
        if self.is_source_pricelist and self.target_pricelist_id:
            self._update_all_target_items()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': 'Los precios han sido sincronizados correctamente.',
                'sticky': False,
                'type': 'success',
            }
        }

    def _sync_item_to_target(self, source_item):
        """Sincroniza un item específico a la lista de precios destino"""
        self.ensure_one()
        if not self.target_pricelist_id:
            return

        source_currency = self.currency_id
        target_currency = self.target_pricelist_id.currency_id

        # Convertir el precio usando el tipo de cambio actual
        converted_price = source_currency._convert(
            source_item.fixed_price,
            target_currency,
            self.env.company,
            fields.Date.today()
        )

        # Buscar si ya existe el item en la lista destino
        target_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', self.target_pricelist_id.id),
            ('product_id', '=', source_item.product_id.id),
            ('min_quantity', '=', source_item.min_quantity)
        ], limit=1)

        if target_item:
            # Actualizar item existente
            target_item.write({
                'fixed_price': converted_price,
                'date_start': source_item.date_start,
                'date_end': source_item.date_end,
            })
        else:
            # Crear nuevo item
            self.env['product.pricelist.item'].with_context(skip_source_sync=True).create({
                'pricelist_id': self.target_pricelist_id.id,
                'product_id': source_item.product_id.id,
                'min_quantity': source_item.min_quantity,
                'fixed_price': converted_price,
                'compute_price': 'fixed',
                'applied_on': '0_product_variant',
                'date_start': source_item.date_start,
                'date_end': source_item.date_end,
            })

    def _update_all_target_items(self):
        """Actualiza todos los items en la lista de precios destino"""
        self.ensure_one()
        if not self.is_source_pricelist or not self.target_pricelist_id:
            return

        for item in self.item_ids:
            self._sync_item_to_target(item)

    @api.model
    def _update_on_currency_rate_change(self):
        """Método para ser llamado cuando cambia el tipo de cambio"""
        source_pricelists = self.search([
            ('is_source_pricelist', '=', True),
            ('target_pricelist_id', '!=', False)
        ])
        for pricelist in source_pricelists:
            pricelist._update_all_target_items()
