from odoo import models, fields, api
from datetime import datetime, timedelta
import requests

class MercadoLibreOrderImporter(models.Model):
    _name = 'mercado.libre.order.importer'
    _description = 'Importador de Pedidos de MercadoLibre'

    @api.model
    def import_orders_last_month(self):
        instance = self.env['vex.instance'].search(['store_type','=','mercadolibre'])  # o selecciona todas si tienes múltiples

        for inst in instance:
            today = datetime.utcnow().date()
            first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day_last_month = today.replace(day=1) - timedelta(days=1)

            from_date = f'{first_day_last_month}T00:00:00.000Z'
            to_date = f'{last_day_last_month}T23:59:59.000Z'

            self._fetch_and_create_orders(inst, from_date, to_date)

    def _fetch_and_create_orders(self, instance, from_date, to_date, limit=50):
        offset = 0
        seller_id = instance.seller_id_meli  # o como tengas definido el seller
        token = instance.meli_access_token  # o la forma como obtienes el token

        while True:
            url = (
                f"https://api.mercadolibre.com/orders/search?seller={seller_id}"
                f"&order.date_created.from={from_date}"
                f"&order.date_created.to={to_date}"
                f"&sort=date_desc&limit={limit}&offset={offset}"
            )
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break  # manejar errores adecuadamente

            data = response.json()
            orders = data.get('results', [])

            if not orders:
                break

            # Procesamiento de pedidos aquí
            for order in orders:
                self.env['sale.order'].create({
                    # estructura basada en el mapeo con el pedido
                })

            offset += limit
