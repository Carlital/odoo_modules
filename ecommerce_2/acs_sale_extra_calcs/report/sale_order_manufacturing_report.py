from odoo import models, api, _


class SaleOrderManufacturingReport(models.AbstractModel):
    # Debe coincidir con: 'report.<modulo>.<id_plantilla_qweb>'
    _name = 'report.acs_sale_extra_calcs.report_manufacturing_order_document'
    _description = 'Reporte de Orden de Fabricación'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)

        # Buscar el usuario con la firma automática activada
        auto_sign_user = self.env['res.users'].search([
            ('auto_sign_on_order_production', '=', True)
        ], limit=1)

        # Agrupar líneas por producto
        grouped_lines = {}
        for order in docs:
            # Usamos manufacturing_order_line_ids para asegurar que solo procesamos las líneas relevantes
            for line in order.manufacturing_order_line_ids:
                # Saltar si no hay producto o si es una línea de sección/nota
                if not line.product_id or line.display_type:
                    continue

                if line.product_id.id not in grouped_lines:
                    grouped_lines[line.product_id.id] = {
                        'product': line.product_id,
                        'lines': [],
                        'lot_names': set(),
                    }

                grouped_lines[line.product_id.id]['lines'].append(line)
                if line.acs_lot_serial and line.acs_lot_serial.name:
                    grouped_lines[line.product_id.id]['lot_names'].add(
                        line.acs_lot_serial.name)

        # Convertir el set de lotes en una cadena de texto ordenada y separada por comas
        for group in grouped_lines.values():
            if group['lot_names']:
                group['lot_numbers_str'] = ', '.join(
                    sorted(list(group['lot_names'])))
            else:
                group['lot_numbers_str'] = ''

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'grouped_lines': grouped_lines,
            'auto_sign_user': auto_sign_user,
        }
