from odoo import api, fields, models
from datetime import datetime, timedelta
import requests
import json
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)
GET_ORDER="https://api.mercadolibre.com/orders/search?seller={}&order.date_created.from={}&order.date_created.to={}&sort=date_desc&limit={}&offset={}"

class VexImportacion(models.Model):
    _name = 'vex.importacion'
    _description = 'Historial de Importaciones por Mes'

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    
    action = fields.Selection([
        ('order', 'Importación de Órdenes'),
        # Otros tipos si fuera necesario
    ], string='Acción', required=True, default='order')

    status = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Completado'),
        ('failed', 'Fallido'),
    ], string='Estado', default='draft')

    vex_instance_id = fields.Many2one(
        'vex.instance', string='Instancia', required=True,
        help='Instancia de MercadoLibre u otra plataforma conectada'
    )

    order_count = fields.Integer(string='Cantidad de Órdenes Importadas', default=0)
    log_message = fields.Text(string='Mensaje de Log / Errores')

    @api.depends('date_from', 'date_to', 'action', 'vex_instance_id')
    def _compute_name(self):
        for rec in self:
            if rec.date_from and rec.action and rec.vex_instance_id:
                mes = rec.date_from.strftime('%B').capitalize()
                anio = rec.date_from.strftime('%Y')
                instancia = rec.vex_instance_id.name
                rec.name = f"{instancia} - {rec.action.upper()} - {mes} {anio}"
            else:
                rec.name = 'Importación'
        
    @api.model
    def cron_generate_order_queue_history(self):
        for instance in self.env['vex.instance'].search([('store_type','=','mercadolibre')]):
            instance.get_access_token()
            # Fecha de inicio de importación (ajústala según necesidad)
            start_date = datetime(2020, 1, 1)
            end_date = datetime.today()

            # Inicializar fecha iteradora
            current_date = start_date
            current_day_count = 1  # Contador de días procesados
            limit = 20  # Límite de órdenes por petición
            total_orders = 0  # Total de órdenes procesadas
            while current_date <= end_date:
                there_is_orders = True
                current_page = 1
                daily_order_count = 0  # Contador de órdenes por día

                date_init_formatted = current_date.strftime('%Y-%m-%dT00:00:00.000-00:00')
                date_end_formatted = current_date.strftime('%Y-%m-%dT23:59:59.000-00:00')

                while there_is_orders:
                    offset = (current_page - 1) * limit
                    url_orders = GET_ORDER.format(instance.meli_user_id, date_init_formatted, date_end_formatted, limit, offset)

                    try:
                        # Realizar la petición a la API
                        response_item = requests.get(url_orders, headers=headers)
                        response_item.raise_for_status()  # Levanta un error si el código de estado no es 2xx
                        if response_item.status_code == 200:
                            json_orders = json.loads(response_item.text)
                            data = json_orders.get("results", [])

                            if data:
                                order_ids = [order['id'] for order in data]
                                order_str = ','.join(map(str, order_ids))

                                # Crear un nuevo registro en vex.import_line con las órdenes
                                new_import_line = self.env['vex.import_line'].create({
                                    'description': order_str,
                                    'status': 'pending',
                                    'instance_id': instance.id,
                                    'action': 'order'
                                })

                                current_page += 1
                                daily_order_count += len(data)  # Incrementar el contador de órdenes por día
                            else:
                                there_is_orders = False
                        else:
                            _logger.warning(f"Error al obtener órdenes: {response_item.status_code} - {response_item.reason}")
                            there_is_orders = False
                    except requests.exceptions.HTTPError as http_err:
                        _logger.error(f"HTTP error al consultar la API: {http_err}")
                        raise ValidationError(f"Error HTTP al consultar la API: {http_err}")
                    except requests.exceptions.RequestException as req_err:
                        _logger.error(f"Error en la conexión con la API: {req_err}")
                        raise ValidationError(f"Error en la conexión con la API: {req_err}")
                    except Exception as e:
                        _logger.error(f"Error desconocido: {e}")
                        raise ValidationError(f"Se produjo un error inesperado: {e}")
                    
                # Almacenar el total de órdenes
                total_orders += daily_order_count
                
                # Loguear el progreso con la fecha actual
                formatted_date = current_date.strftime('%d/%m/%Y')  # Formato DD/MM/YYYY
                _logger.info(f"Fecha {formatted_date} procesada - Ordenes obtenidas: {daily_order_count}")

                # Avanzar al siguiente día
                current_date += timedelta(days=1)
                current_day_count += 1  # Incrementar el contador de días procesados
                
            # Loguear el total de órdenes procesadas al final
            _logger.info(f"Total de órdenes importadas: {total_orders}")

            # Calcular fin del mes
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

            _logger.info(f"Cola de pedidos generada para el mes: {current_date.strftime('%Y-%m')}")

            # Avanzar al siguiente mes
            current_date = next_month

    def import_orders_from_2020(self):
        limit = 20
        start_date = datetime(2020, 1, 1)
        end_date = datetime.today()

        for instance in self.env['vex.instance'].search([('store_type', '=', 'mercadolibre')]):
            instance.get_access_token()
            headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Bearer {instance.meli_access_token}'}

            current_date = start_date
            total_orders_all = 0

            _logger.info(f"Inicio instancia {instance.name}")

            while current_date <= end_date:
                date_init = current_date.strftime('%Y-%m-%dT00:00:00.000-00:00')
                date_end = current_date.strftime('%Y-%m-%dT23:59:59.000-00:00')
                page = 0
                daily_order_count = 0
                more_orders = True

                while more_orders:
                    offset = page * limit
                    url_orders = GET_ORDER.format(
                        instance.meli_user_id, date_init, date_end, limit, offset
                    )

                    try:
                        response = requests.get(url_orders, headers=headers)
                        response.raise_for_status()
                        data = response.json().get("results", [])

                        if not data:
                            more_orders = False
                            break
                        
                        order_ids = [order['id'] for order in data]
                        _logger.info(f"Ordenes encontradas: {order_ids}")
                        order_str = ','.join(map(str, order_ids))

                        self.env['vex.import_line'].create({
                            'description': order_str,
                            'status': 'pending',
                            'instance_id': instance.id,
                            'action': 'order'
                        })

                        daily_order_count += len(data)
                        page += 1

                    except requests.exceptions.RequestException as err:
                        _logger.error(f"Error al consultar API para {current_date}: {err}")
                        raise ValidationError(f"Error de conexión o datos: {err}")
                    except Exception as e:
                        _logger.error(f"Error inesperado: {e}")
                        raise ValidationError(f"Error inesperado: {e}")

                _logger.info(f"{current_date.strftime('%Y-%m-%d')} - Órdenes obtenidas: {daily_order_count}")
                total_orders_all += daily_order_count
                current_date += timedelta(days=1)

            _logger.info(f"Total órdenes importadas para la instancia {instance.name}: {total_orders_all}")
