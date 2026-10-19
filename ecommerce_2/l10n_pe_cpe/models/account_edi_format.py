# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError
import base64
import re
from datetime import datetime
from librecpe.cpe import Cliente
import requests

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'
    
    def _is_compatible_with_journal(self, journal):
        self.ensure_one()
        res = super()._is_compatible_with_journal(journal)
        if self.code != 'pe_cpe':
            return res
        return journal.type == 'sale'

    def _get_move_applicability(self, move):
        self.ensure_one()
        if self.code != 'pe_cpe':
            return super()._get_move_applicability(move)
        res = {}
        if move.pe_is_cpe:
            res = {
                'post': self._pe_post_cpe,
                #'cancel': self._pe_cancel_cpe,
                #'cancel_batching': move,
                'edi_content': self._pe_xml_cpe,
            }
        return res

    def _pe_post_cpe(self, move_id):
        vals = {}
        pe_digest = False
        attachment_id = False
        xml_content = False
        if move_id.company_id.pe_ws_server in ['sunat']:
            data = self.env['pe.cpe.send'].get_document(move_id)
            xml_name =  move_id._pe_cpe_document_name(move_id)
            xml_content = data.get('xml_firmado')
            attachment_id = self.env['ir.attachment'].create({
                'name': "%s.xml" % xml_name,
                'datas': xml_content,
                'mimetype': 'application/xml',
                'res_field': 'attachment_id',
            })
            pe_digest = data.get('resumen', False)
            vals['attachment'] = attachment_id.id
        edi_document_ids = move_id.edi_document_ids.filtered(lambda s: s.edi_format_id.code == 'pe_cpe')
        edi_document_id = edi_document_ids and edi_document_ids[0] or False
        try:
            edi_document_id.action_sent(attachment_id, pe_digest, xml_content)
            if edi_document_id.pe_return_code == '0000':
                vals['success'] = True
            else:
                vals['error'] = edi_document_id.pe_response
        except Exception:
            pass
        return {move_id: vals}

    def _pe_cancel_cpe(self, move_id):
        return {}
    def _pe_xml_cpe(self, move_id):
        res = False
        if move_id.company_id.pe_ws_server in ['sunat']:
            res = self.env['pe.cpe.send'].get_document(move_id).get('xml_firmado')
        return res

    def _pe_check_response(self, response):
        self.ensure_one()
        vals = {}
        if response.get('codigo'):
            if self.env['pe.catalog.return'].get_by_code(response.get('codigo')):
                vals['pe_return_code'] = response.get('codigo')
        if response.get('respuesta'):
            vals['pe_response'] = response.get('respuesta')
        if response.get('nota'):
            vals['pe_note'] = response.get('nota')
        res = ""
        if response.get('faultcode'):
            code = response.get('faultcode', '').split(".")[-1]
            if self.env['pe.catalog.return'].get_by_code(code):
                vals['pe_return_code'] = code
            vals['pe_response'] = response.get('faultcode')
            res = "%s "  % response.get('faultcode')
        if response.get('faultstring'):
            res += response.get('faultstring', "")
        if res:
            vals['pe_note'] = str(res)
        return vals

    def _export_pe_cpe(self, move_id):
        vals = {}
        return vals
    
    def _check_move_configuration(self, move):
        self.ensure_one()
        if self.code != 'pe_cpe':
            return super(AccountEdiFormat, self)._check_move_configuration(move)
        res = []
        company_id = move.company_id.parent_id or move.company_id
        date_due = move.invoice_date_due or fields.Date.context_today(self)
        date_invoice = move.invoice_date or fields.Date.context_today(self)
        if (date_due - date_invoice).days > 0 and not move.pe_payment_lines:
            move.generate_pe_fees()
        elif (date_due - date_invoice).days <= 0 and move.pe_payment_lines:
            if move.journal_id.pe_invoice_code not in ['07'] and move.pe_credit_note_code not in ['13']:
                move.pe_payment_lines.unlink()
        company_id = move.company_id
        if not company_id.pe_ws_type:
            res.append(_("The type of server is required"))
        if not company_id.pe_ws_server:
            res.append(_("The server is required"))
        if not company_id.pe_ws_url:
            res.append(_("The url of server is required"))
        if not company_id.pe_ws_status_url and company_id.pe_ws_server in ['sunat']:
            res.append(_("The url status of server is required"))
        if not company_id.pe_ws_user and company_id.pe_ws_server in ['sunat']:
            res.append(_("The user of server is required"))
        if not company_id.pe_ws_password:
            res.append(_("The password of server is required"))
        if not company_id.pe_private_key and company_id.pe_ws_server in ['sunat']:
            res.append(_("The private key is required"))
        if not company_id.pe_public_key and company_id.pe_ws_server in ['sunat']:
            res.append(_("The public key is required"))
        
        if move.journal_id.pe_invoice_code not in ['01', '03', '07', '08']:
            res.append("Documento no soportado, solo es posible emitir Facturas, Boletas, Notas de Credito y Debito")
        if move.pe_invoice_code != move.journal_id.pe_invoice_code:
            res.append("El tipo de documento no coincide con el diario")
        if move.move_type == 'out_invoice' and move.pe_invoice_code in ['07']:
            res.append("El tipo de documento no puede ser 07, Nota de Credito.")
        if move.move_type == 'out_refund' and move.pe_invoice_code not in ['07']:
            res.append("El tipo de documento debe ser 07, Nota de Credito.")
        if (move.pe_operation_type and move.pe_operation_type[:2]=="02"):
            for line in move.invoice_line_ids:
                if line.display_type and line.display_type in ['line_section', 'line_note']:
                    continue
                if line.pe_type_affectation!="40":
                    res.append("El tipo de afectacion del producto %s debe ser Exportacion" %line.name)

        if move.journal_id.pe_invoice_code in ['07'] and move.pe_credit_note_code in ['13'] and move.amount_total != 0.0:
            res.append("El monto total de la Nota de Credito debe ser 0.0")
        if move.journal_id.pe_invoice_code in ['07'] and move.pe_credit_note_code in ['13'] and not move.pe_payment_lines:
            res.append("Es necesario registrar la Corrección del monto neto pendiente de pago y/o la(s) fechas(s) de vencimiento del pago")
        if move.journal_id.pe_invoice_code not in ['07'] and move.pe_credit_note_code not in ['13']:
            for line in move.invoice_line_ids:
                if line.display_type and line.display_type in ['line_section', 'line_note']:
                    continue
                if not line.product_id and not line.is_downpayment:
                    res.append("Debe definir el producto %s " %line.name)
                if not line.product_id.default_code and not line.is_downpayment:
                    res.append("El producto %s no tiene codigo" %line.name)
                if line.quantity==0.0 or line.price_unit == 0.0:
                    res.append("La cantidad o precio del producto %s debe ser mayor a 0.0" %line.name)
                if not line.tax_ids and line.quantity>0:
                    res.append("Es Necesario definir por lo menos un impuesto para el pruducto %s" %line.name)
                if line.product_id.pe_require_plate and not (line.pe_license_plate):
                    res.append("Es Necesario registrar el numero de placa para el pruducto %s" %line.name)
                if not line.pe_type_affectation:
                    res.append("Es Necesario el tipo de afectacion para el pruducto %s" %line.name)
        if not re.match(r'^(B|F){1}[A-Z0-9]{3}\-\d+$', move.l10n_latam_document_number):
            res.append("El numero de la factura ingresada no cumple con el estandar.\n"\
                            "Verificar la secuencia del Diario por ejemplo F001- o BN01-. \n"\
                            "Para cambiar ir a Configuracion/Contabilidad/Diarios/Secuencia del asiento")

        if move.pe_invoice_code in ['03'] or move.reversed_entry_id.pe_invoice_code in ['03'] or move.debit_origin_id.pe_invoice_code in ['03']:
            doc_type = move.partner_id.pe_doc_type or '-'
            doc_number = move.partner_id.pe_doc_number or '-'
            if doc_type == '6' and doc_number[:2]!='10':
                res.append("El dato ingresado no cumple con el estandar \nTipo: %s \nNumero de documento: %s\n"\
                                "Deberia emitir una Factura. Cambiar en Factura/Otra Informacion/Diario"%(doc_type, doc_number))
            amount = company_id.pe_max_amount or 0
            if move.amount_total >= amount and (doc_type=='-' or doc_number=='-'):
                res.append("El dato ingresado no cumple con el estandar \nTipo: %s \nNumero de documento: %s\nSon obligatorios el Tipo de Doc. y Numero"%(doc_type, doc_number))
            if move.amount_total >= amount and move.partner_id.vat == '00000000':
                res.append("El cliente debe tener un numero de documento de identidad valido")
        if move.pe_invoice_code in ['01'] or move.reversed_entry_id.pe_invoice_code in ['01'] or move.debit_origin_id.pe_invoice_code in ['01']:
            doc_type = move.partner_id.pe_doc_type or move.partner_id.parent_id.pe_doc_type or '-'
            doc_number = move.partner_id.pe_doc_number or move.partner_id.parent_id.pe_doc_number or '-'
            if doc_type not in ["0", '6'] or not doc_number:
                res.append(" El numero de documento de identidad del receptor debe ser RUC \nTipo: %s \nNumero de documento: %s"%(doc_type, doc_number))
        invoice_date = move.pe_invoice_date.date()
        today = fields.Datetime.context_timestamp(self, datetime.now())
        days = today.date() - invoice_date
        if days.days>move.company_id.pe_max_days and (move.pe_invoice_code in ['01'] or move.reversed_entry_id.pe_invoice_code in ['01']):
            res.append("La fecha de emision no puede ser menor a %d dias de hoy ni mayor a la fecha de hoy." % move.company_id.pe_max_days)
        if days.days<0:
            res.append("La fecha de emision no puede ser menor a %d dias de hoy ni mayor a la fecha de hoy." % move.company_id.pe_max_days)
        if move.pe_subject_detraction and not move.company_id.pe_detraction_account_number:
            res.append("Debe registrar la cuenta de Detracciones en Compañias")
        if not move.ref and move.pe_invoice_code in ['07', '08']:
            res.append("Es necesario el motivo de la nota de Credito/Debito")
        if move.invoice_line_ids.filtered(lambda l: l.product_id.pe_product_type in ['prepayment'] and not l.pe_prepaid_invoice_id and l.quantity<0):
            res.append("Es necesario registrar la factura de anticipo")
        if move.pe_invoice_code in ['07'] and not move.pe_reversed_entry_id:
            res.append("Es necesario la factura de origen")
        if move.pe_invoice_code in ['08'] and not move.pe_reversed_entry_id:
            res.append("Es necesario la factura de origen")
        if move.pe_invoice_code != move.journal_id.pe_invoice_code:
            res.append("El tipo de documento no coincide con el diario")
        if move.invoice_line_ids.filtered(lambda l: l.pe_prepaid_invoice_id and l.pe_type_affectation not in ['10', '20', '30', '40']):
            res.append("El anticipo debe tener codigo de afectacion 10, 20, 30 o 40")

        return res
            
        