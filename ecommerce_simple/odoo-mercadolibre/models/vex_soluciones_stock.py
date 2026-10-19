from odoo import models, api
import requests
import logging
import json

_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    """ @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for quant in records:
            quant._update_meli_stock()
        return records

    def write(self, vals):
        res = super().write(vals)
        for quant in self:
            quant._update_meli_stock()
        return res """

    def _update_meli_stock(self):
        for quant in self:
            product_variant = quant.product_id
            product_template = quant.product_id.product_tmpl_id

            if not product_template.server_meli or not product_template.ml_publication_code:
                continue

            instance = product_template.instance_id
            if not instance or not instance.meli_access_token:
                _logger.warning(f"Instancia ML no configurada para producto {product_template.name}")
                continue
            
            item_id = product_template.ml_publication_code
            instance.get_access_token()
            access_token = instance.meli_access_token
            url = f"https://api.mercadolibre.com/items/{item_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                    "available_quantity": int(quant.quantity)
                }
            try:
                #response = requests.put(url, headers=headers, data=json.dumps(payload))
                _logger.info(f"{instance.name} [ML STOCK UPDATED] Producto {product_template.name} -> {quant.quantity} unidades")
                return True
                if response.status_code not in [200, 201]:
                    _logger.error(f"[ML STOCK ERROR] {response.status_code}: {response.text}")
                else:
                    _logger.info(f"[ML STOCK UPDATED] Producto {product_template.name} -> {quant.quantity} unidades")

            except Exception as e:
                _logger.exception(f"Error actualizando stock en MercadoLibre: {e}")

class StockChangeProductQty(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    def change_product_qty(self):
        res = super().change_product_qty()

        for wizard in self:
            product = wizard.product_id
            product_template = product.product_tmpl_id

            """ if not product_template.server_meli or not product_template.ml_publication_code:
                continue

            instance = product_template.instance_id
            if not instance or not instance.meli_access_token:
                continue

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id)
            ])

            for quant in quants:
                quant._update_meli_stock() """
            
            product_template._update_meli_stock_only_once()

        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            product_templates = picking.move_ids.mapped('product_id.product_tmpl_id')

            for template in product_templates.filtered(lambda p: p.server_meli and p.ml_publication_code):
                instance = template.instance_id
                if not instance or not instance.meli_access_token:
                    continue

                item_id = template.ml_publication_code
                instance.get_access_token()
                access_token = instance.meli_access_token
                url = f"https://api.mercadolibre.com/items/{item_id}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }

                total_qty = sum(template.product_variant_ids.mapped('qty_available'))
                payload = {"available_quantity": int(total_qty)}

                try:
                    requests.put(url, headers=headers, data=json.dumps(payload))
                    _logger.info(f"[ML STOCK] Producto {template.name} actualizado tras validar picking: {total_qty}")
                except Exception as e:
                    _logger.exception(f"Error actualizando stock ML tras picking: {e}")

        return res