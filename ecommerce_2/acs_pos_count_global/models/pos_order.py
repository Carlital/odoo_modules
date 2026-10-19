import logging

from odoo import fields, models, api
from datetime import datetime, timedelta, timezone

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def compute_all_order_count(self):
        user_id = self.env.user
        if user_id.tz_offset:
            minutes = int(user_id.tz_offset[0:2]) * 60 + int(user_id.tz_offset[1:3])*60
            sign = user_id.tz_offset[0]
            if sign == '-':
                minutes = -minutes
        else:
            minutes = 0

        ecuador_offset = timezone(timedelta(minutes=minutes))
        today = datetime.now(ecuador_offset).date()
        orders_data = self.env['pos.order'].search([('date_order', '>=', today.strftime('%Y-%m-%d'))])
        
        all_order_count = 0
        for order in orders_data:
            date_order = order.date_order + timedelta(minutes=minutes)
            if date_order.date() == today:
                all_order_count += 1

        return all_order_count

    def _send_notification(self, data):
        # Send a notification to the point of sale channel to indicate that the transaction are finish
        pos_session_sudo = data.session_id
        if pos_session_sudo:
            pos_session_sudo.config_id._notify('ACS_POS_COUNT_GLOBAL', {
                'config_id': pos_session_sudo.config_id.id,
                'count':self.compute_all_order_count()
            })
    @api.model_create_multi
    def create(self, vals_list):
        res =  super().create(vals_list)
        res._send_notification(res)
        return res


class PosSession(models.Model):
    _inherit = 'pos.session'

    
    def compute_all_order_count(self):
        today = datetime.now().date()
        orders_data = self.env['pos.order'].search([('date_order', '>=', today.strftime('%Y-%m-%d'))])
        user_id = self.env.user
        if user_id.tz_offset:
            minutes = int(user_id.tz_offset[0:2]) * 60 + int(user_id.tz_offset[1:3])*60
            sign = user_id.tz_offset[0]
            if sign == '-':
                minutes = -minutes
        else:
            minutes = 0
        all_order_count = 0
        for order in orders_data:
            date_order = order.date_order + timedelta(minutes=minutes)
            if date_order.date() == today:
                all_order_count += 1
        # self._cr.execute(f"select count(*) as orders_today from pos_order where date_order >= '{today}'")
        # result = self._cr.dictfetchall()
        for r in self: 
            r.order_count = all_order_count

    order_count = fields.Integer(string="Contador de ordenes",compute="compute_all_order_count")

    def _load_pos_data_fields(self,config_id):
        result = super()._load_pos_data_fields(config_id)
        # result["search_params"]["fields"].append("order_count")
        result.append("order_count")
        return result