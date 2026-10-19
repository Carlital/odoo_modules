# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _get_price_from_line(self, purchase_id, sale_id, pos_order_id):
        self.ensure_one()
        if sale_id:
            uom_id = self.product_id.uom_id
            line_ids = sale_id.order_line.filtered(
                lambda x: self.product_id.id == x.product_id.id and self.quantity == x.product_uom_qty and self.product_uom_id.id == x.product_uom.id)
            if line_ids:
                if len(line_ids):
                    return line_ids.price_unit
            else:
                line_ids = sale_id.order_line.filtered(
                    lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom.ratio * x.product_uom_qty))
                if line_ids:
                    if len(line_ids):
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price
        elif purchase_id:
            line_ids = purchase_id.order_line.filtered(
                lambda x: self.product_id.id == x.product_id.id and self.quantity == x.product_uom_qty and self.product_uom_id.id == x.product_uom.id)
            if line_ids:
                if len(line_ids) == 1:
                    return line_ids.price_unit
            else:
                line_ids = purchase_id.order_line.filtered(
                    lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom.ratio * x.product_uom_qty))
                if line_ids:
                    if len(line_ids) == 1:
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price
        elif pos_order_id:
            line_ids = pos_order_id.lines.filtered(
                lambda x: self.product_id.id == x.product_id.id and self.quantity == x.qty and self.product_uom_id.id == x.product_uom_id.id)
            if line_ids:
                if len(line_ids) == 1:
                    return line_ids.price_unit
            else:
                line_ids = pos_order_id.lines.filtered(
                    lambda x: self.product_id.id == x.product_id.id and self.quantity == (x.product_uom_id.ratio * x.qty))
                if line_ids:
                    if len(line_ids) == 1:
                        return line_ids.price_unit/self.quantity
            return self.product_id.list_price

    def _compute_saldo_stock(self):
        """
        Calcula el saldo de stock, precio, documento y socio para las líneas de movimiento.
        El saldo de stock se calcula por producto y por almacén para garantizar la exactitud
        en un entorno de múltiples almacenes.
        """
        # Inicializa todos los campos para los registros en el recordset actual.
        # Esto asegura que las líneas sin almacén o sin datos tengan valores predeterminados.
        for record in self:
            record.stock_balance = 0
            record.price_unit_history = 0
            record.document = record.picking_id.origin if record.picking_id else (
                record.move_id.reference or '')
            record.partner_id = False

        # 1. PREPARACIÓN: Crear un mapa de ubicación -> almacén para evitar búsquedas repetitivas.
        all_warehouses = self.env['stock.warehouse'].search([])
        location_warehouse_map = {}
        for wh in all_warehouses:
            wh_locations = self.env['stock.location'].search([
                ('id', 'child_of', wh.view_location_id.id),
                ('usage', '=', 'internal')
            ])
            for loc in wh_locations:
                if loc.id not in location_warehouse_map:
                    location_warehouse_map[loc.id] = wh.id

        # 2. AGRUPACIÓN: Agrupar los IDs de las líneas a calcular por (producto, almacén).
        lines_to_compute_by_group = defaultdict(set)
        lines_map = {line.id: line for line in self}

        for line in self:
            warehouse_id = location_warehouse_map.get(line.location_dest_id.id)
            if not warehouse_id:
                warehouse_id = location_warehouse_map.get(line.location_id.id)

            if warehouse_id:
                key = (line.product_id.id, warehouse_id)
                lines_to_compute_by_group[key].add(line.id)

        # 3. CÁLCULO POR GRUPO: Iterar sobre cada grupo (producto, almacén) y calcular su historial completo.
        for (product_id, warehouse_id), line_ids_to_update in lines_to_compute_by_group.items():
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            wh_locations = self.env['stock.location'].search([
                ('id', 'child_of', warehouse.view_location_id.id),
                ('usage', '=', 'internal')
            ])
            wh_location_ids = wh_locations.ids

            # Obtener TODAS las líneas de movimiento para este grupo, ordenadas cronológicamente.
            all_lines_for_group = self.env['stock.move.line'].search([
                ('product_id', '=', product_id),
                ('state', '=', 'done'),
                '|',
                ('location_id', 'in', wh_location_ids),
                ('location_dest_id', 'in', wh_location_ids),
            ], order='id asc')

            current_balance = 0.0
            for line in all_lines_for_group:
                is_in = line.location_dest_id.id in wh_location_ids
                is_out = line.location_id.id in wh_location_ids

                # Actualizar el saldo corriente
                if is_in and not is_out:
                    current_balance += line.quantity
                elif is_out and not is_in:
                    current_balance -= line.quantity
                # Si es un movimiento interno dentro del mismo almacén, el saldo no cambia.

                # 4. ASIGNACIÓN: Si esta línea es una de las que necesitamos actualizar, asignamos los valores.
                if line.id in line_ids_to_update:
                    r = lines_map[line.id]
                    r.stock_balance = current_balance

                    # Asignar el resto de los campos calculados para este registro
                    r.document = r.picking_id.origin if r.picking_id else (
                        r.move_id.reference or '')
                    if r.picking_code == 'incoming':
                        r.partner_id = r.picking_id.partner_id if r.picking_id else False
                        if r.picking_id and r.picking_id.purchase_id:
                            r.price_unit_history = r._get_price_from_line(
                                r.picking_id.purchase_id, False, False)
                        else:
                            r.price_unit_history = r.product_id.list_price
                    elif r.picking_code == 'outgoing':
                        r.partner_id = r.picking_id.partner_id if r.picking_id else False
                        if r.picking_id:
                            if r.picking_id.pos_session_id:
                                r.price_unit_history = r._get_price_from_line(
                                    False, False, r.picking_id.pos_order_id)
                            elif r.picking_id.sale_id:
                                r.price_unit_history = r._get_price_from_line(
                                    False, r.picking_id.sale_id, False)
                            else:
                                r.price_unit_history = r.product_id.list_price
                        else:
                            r.price_unit_history = r.product_id.list_price
                    else:  # Movimientos internos, de fabricación, ajustes, etc.
                        r.partner_id = False
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
