from odoo import api, models, fields, exceptions, _
import base64
import io
import pandas as pd

class MercadoLibreProductWizard(models.TransientModel):
    _name = 'mercado.libre.product.massive.wizard'
    _description = 'Importar reglas MercadoLibre'

    file = fields.Binary(string="Archivo Excel")
    filename = fields.Char(string="Nombre del archivo")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self._get_currency())

    def download_template(self):
        df = pd.DataFrame(columns=['num_publication', 'min_price', 'max_price'])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'template_max_min.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(buf.read()),
            'res_model': 'mercado.libre.product.massive.wizard',
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def action_import_template(self):
        current_user = self.env.user 
        meli_instance = current_user.meli_instance_id
        if not self.file:
            raise exceptions.UserError(_('Please upload a file before importing.'))

        try:
            buf = io.BytesIO(base64.b64decode(self.file))
            df = pd.read_excel(buf)
        except Exception as e:
            raise exceptions.UserError(_('Error reading file: %s') % e)

        required_columns = {'num_publication', 'min_price', 'max_price'}
        if not required_columns.issubset(df.columns):
            raise exceptions.UserError(_('The file must contain the columns: num_publication, min_price, max_price'))

        for _, row in df.iterrows():
            if pd.isna(row['num_publication']) or pd.isna(row['min_price']) or pd.isna(row['max_price']):
                continue

            product = self.env['product.template'].search([('default_code', '=', row['num_publication']), ('instance_id', '=', meli_instance.id)], limit=1)
            if product:
                existing_rule = self.env['mercado.libre.product'].search([('product_id', '=', product.id), ('instance_id', '=', meli_instance.id)], limit=1)
                if existing_rule:
                    existing_rule.write({
                        'precio_min': row['min_price'],
                        'precio_max': row['max_price'],
                        'type_rule': 'auto',
                        'state_publi': 'activo',
                        'is_automatic_type': True,
                        'text_publi': f"minimum {self.currency_id.symbol} {row['min_price']} and maximum {self.currency_id.symbol} {row['max_price']}",
                        'price_score': None,
                        'price_score_badge': None,
                        'new_price': 0.00
                    })
                else:
                    self.env['mercado.libre.product'].create({
                        'product_id': product.id,
                        'product': product.id,
                        'precio_min': row['min_price'],
                        'precio_max': row['max_price'],
                        'type_rule': 'auto',
                        'state_publi': 'activo',
                        'is_automatic_type': True,
                        'state_publi': 'activo',
                        'text_publi': f"minimum {self.currency_id.symbol} {row['min_price']} and maximum {self.currency_id.symbol} {row['max_price']}"
                    })

    @api.model
    def _get_currency(self):
        instance = self.env.user.meli_instance_id
        if instance and instance.meli_default_currency:
            Currency = self.env['res.currency']

            currency = Currency.with_context(active_test=False).sudo().search(
                [('name', '=', instance.meli_default_currency)],
                limit=1
            )
            if not currency:
                if 'currency_code' in Currency._fields:
                    currency = Currency.search([('currency_code', '=', instance.meli_default_currency)], limit=1)
                    if currency:
                        print(f"Moneda encontrada por currency_code: {currency.name}")
            else:
                print(f"Moneda encontrada: {currency.name} ({currency.symbol})")
            
            return currency.id if currency else None

        return None



                