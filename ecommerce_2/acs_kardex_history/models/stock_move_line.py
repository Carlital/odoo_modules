# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    

    def _get_price_from_line(self,purchase_id,sale_id,pos_order_id):
        self.ensure_one()
        if sale_id:
            uom_id = self.product_id.uom_id
            line_ids = sale_id.order_line.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == x.product_uom_qty and self.product_uom_id.id == x.product_uom.id)
            if line_ids:
                if len(line_ids):
                    return line_ids.price_unit
            else:
                line_ids = sale_id.order_line.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom.ratio * x.product_uom_qty))
                if line_ids:
                    if len(line_ids):
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price
        elif purchase_id:
            line_ids = purchase_id.order_line.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == x.product_uom_qty and self.product_uom_id.id == x.product_uom.id)
            if line_ids:
                if len(line_ids)==1:
                    return line_ids.price_unit
            else:
                line_ids = purchase_id.order_line.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom.ratio * x.product_uom_qty))
                if line_ids:
                    if len(line_ids) ==1:
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price
        elif pos_order_id:
            line_ids = pos_order_id.lines.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == x.qty and self.product_uom_id.id == x.product_uom_id.id)
            if line_ids:
                if len(line_ids) == 1:
                    return line_ids.price_unit
            else:
                line_ids = pos_order_id.lines.filtered(lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom_id.ratio * x.qty))
                if line_ids:
                    if len(line_ids) == 1:
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price
            
    # @api.depends('quantity','location_id','location_dest_id')
    def _compute_saldo_stock(self):
        for r in self.sorted(key=lambda record: record.id):
            # Tenemos estos códigos
            # |  incoming  |  outgoing  |  internal     |
            # |  Suma      |  Resta     |  No hace nada |
            last_record_id = self.env['stock.move.line'].search([('id','<',r.id),('product_id','=',r.product_id.id),('state','=','done')],order="id desc",limit=1)
            r.document = r.picking_id.origin
            
            if not last_record_id:
                if r.picking_code == 'incoming':
                    r.partner_id = r.picking_id.partner_id.id
                    r.stock_balance = r.quantity
                    if r.picking_id.purchase_id:
                        r.price_unit_history = r._get_price_from_line(r.picking_id.purchase_id,False,False)
                    else:
                        r.price_unit_history = r.product_id.list_price
                elif r.picking_code == 'outgoing':
                    r.partner_id = r.picking_id.partner_id.id
                    r.stock_balance = -r.quantity
                    if r.picking_id.pos_session_id:
                        r.price_unit_history = r._get_price_from_line(False,False,r.picking_id.pos_order_id)
                    elif r.picking_id.sale_id:
                        r.price_unit_history = r._get_price_from_line(False,r.picking_id.sale_id,False)
                    else:
                        r.price_unit_history = r.product_id.list_price
                    
                else:
                    r.partner_id = False
                    if r.picking_id:
                        if r.location_dest_id.location_id:
                            r.stock_balance = r.quantity
                            r.price_unit_history = r.product_id.list_price
                        else:
                            r.stock_balance = -r.quantity
                            r.price_unit_history = r.product_id.list_price
                    else:
                        if r.location_id.usage == 'inventory' and r.location_dest_id.usage == 'internal':
                            r.stock_balance = r.quantity
                            r.price_unit_history = r.product_id.standard_price
                        elif r.location_id.usage == 'internal' and r.location_dest_id.usage == 'inventory':
                            r.stock_balance = -r.quantity
                            r.price_unit_history = r.product_id.standard_price
            else:
                if r.picking_code == 'incoming':
                    r.partner_id = r.picking_id.partner_id.id
                    r.stock_balance = last_record_id.stock_balance + r.quantity
                    if r.picking_id.purchase_id:
                        r.price_unit_history = r._get_price_from_line(r.picking_id.purchase_id,False,False)
                    else:
                        r.price_unit_history = r.product_id.list_price
                elif r.picking_code == 'outgoing':
                    r.partner_id = r.picking_id.partner_id.id
                    r.stock_balance = last_record_id.stock_balance - r.quantity
                    if r.picking_id.pos_session_id:
                        r.price_unit_history = r._get_price_from_line(False,False,r.picking_id.pos_order_id)
                    elif r.picking_id.sale_id:
                        # line_id = r.picking_id.sale_id.order_line.filtered(lambda rec: rec.product_id.id == r.product_id.id)
                        r.price_unit_history = r._get_price_from_line(False,r.picking_id.sale_id,False)
                    else:
                        r.price_unit_history = r.product_id.list_price
                    
                else:
                    if r.picking_id:
                        r.partner_id = False
                        if r.location_dest_id.location_id:
                            r.stock_balance = last_record_id.stock_balance
                            r.price_unit_history = r.product_id.standard_price
                        else:
                            r.stock_balance = last_record_id.stock_balance -r.quantity
                            r.price_unit_history = r.product_id.standard_price
                    else:
                        r.partner_id = False
                        if r.location_id.usage == 'inventory' and r.location_dest_id.usage == 'internal':
                            r.stock_balance = last_record_id.stock_balance + r.quantity
                            r.price_unit_history = r.product_id.standard_price
                        elif r.location_id.usage == 'internal' and r.location_dest_id.usage == 'inventory':
                            r.stock_balance = last_record_id.stock_balance - r.quantity
                            r.price_unit_history = r.product_id.standard_price
    
    stock_balance = fields.Float(
        string='Saldo Stock',
        compute="_compute_saldo_stock",
        # store=True
    )
    
    price_unit_history = fields.Float(
        string='Precio',
        compute="_compute_saldo_stock",
        # store=True
    )
    document = fields.Char(
        string='Documento',
        compute="_compute_saldo_stock"
    )
    partner_id = fields.Many2one(
        string='Socio',
        comodel_name='res.partner',
        compute="_compute_saldo_stock",
    )
    
    

