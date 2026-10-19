from librecpe import Documento
from odoo import fields, models
import pytz

class PeElectronicGuideSend(models.AbstractModel):
    
    _name = "pe.electronic.guide.send"
    _description = "Send Document"
    
    def _empresa(self, partner_id):
        vals = {}
        vals['nombre'] = partner_id.legal_name and partner_id.legal_name!='-' and partner_id.legal_name or partner_id.name
        vals['nomComercial'] = partner_id.commercial_name and partner_id.commercial_name!='-' and partner_id.commercial_name or ""
        vals['tipoDocumento'] = partner_id.doc_type or '-'
        vals['numDocumento'] = partner_id.doc_number or '-'
        vals['direccion'] = partner_id.street or ''
        vals['urbanizacion'] = partner_id.street2 or ''
        vals['ubigeo'] = partner_id.district_id.code or ''
        vals['distrito'] = partner_id.district_id.name or ''
        vals['provincia'] = partner_id.province_id.name or ''
        vals['region'] = partner_id.state_id.name or ''
        vals['codPais'] = partner_id.country_id.code or ''
        vals['email'] = partner_id.email or ''
        return vals

    def _get_emisor(self, company_id, user_id = False, branch_code = False):
        partner_id = company_id.partner_id
        vals = self._empresa(partner_id)
        vals.update({'codEstablecimiento': branch_code or company_id.pe_branch_code or ''})
        return {'emisor':vals}

    def _transportista(self, partner_id):
        vals = self._empresa(partner_id)
        vals['licencia'] = partner_id.pe_driver_license or ''
        vals['nomPersona'] = partner_id.name.split(",")[-1] or ''
        vals['apPaterno'] = partner_id.name.split(",")[0].split(" ")[0] or ''
        vals['numRegistro'] = partner_id.pe_register_number or ''
        return vals

    def _get_detalles_guia(self, line_ids):
        res = []
        for line_id in line_ids:
            vals = {}
            vals['cantidad'] = line_id.quantity
            vals['codUnidadMedida'] = line_id.uom_code or 'NIU'
            vals['descripcion'] = line_id.name
            vals['codProducto'] = line_id.product_code or ''
            res.append(vals)
        return res

    def _get_eguide_document(self, guide_id, key, crt):
        vals = {}
        vals['numero'] = guide_id.name
        vals['tipoDocumento'] = '09'
        vals['observacion'] = guide_id.note or ''
        timezone = pytz.timezone("America/Lima")
        localtimezone = pytz.timezone("UTC")
        date_issue = fields.Datetime.from_string(guide_id.date_issue).replace(tzinfo=localtimezone) # or fields.Datetime.now()
        vals['fecEmision'] = fields.Datetime.to_string(date_issue.astimezone(timezone)) or ''
        vals.update(self._get_emisor(guide_id.company_id))
        relacionados = []
        for related in guide_id.related_ids:
            relacionados.append(
                {'numero': related.name,
                 'tipoDocumento': related.document_type,
                 'emisor': self._empresa(related.partner_id)}
            )

        vals['documentosRelacionados'] = relacionados
        vals['codSucursal'] = guide_id.src_branch_id.code or guide_id.dst_branch_id.code or '0000'
        if guide_id.reason_transfer in ['02', '04', '06', '08']: # Revisar
            sender_id = guide_id.partner_id
            partner_id = guide_id.company_id.partner_id
        else:
            sender_id = guide_id.company_id.partner_id
            partner_id = guide_id.partner_id

        vals['remitente'] = self._empresa(sender_id)
        vals['destinatario'] = self._empresa(partner_id)
        # if guide_id.supplier_id:
        #     vals['establecimientoTercero'] = self._empresa(guide_id.supplier_id)
        vals['motivo'] = guide_id.reason_transfer
        vals['descripcion'] = guide_id.description or ''
        vals['vehiculoM1L'] = guide_id.vehicle_m1_l
        vals['transbordo'] = guide_id.is_programmed
        vals['pesoBruto'] = guide_id.gross_weight
        vals['bultos'] = guide_id.unit_quantity
        vals['modoTraslado'] = guide_id.transport_mode or ''
        vals['fechaTraslado'] = guide_id.transfer_date
        transportistas = []
        if guide_id.carrier_id:
            transportistas.append(self._transportista(guide_id.carrier_id))
        for carrier_id in guide_id.carrier_ids:
            transportistas.append(self._transportista(carrier_id.driver_id))
        vals['transportistas'] = transportistas
        placa = guide_id.vehicle_ids and guide_id.vehicle_ids[0].name or ''
        vals['placa'] = placa and placa.replace("-", "") or placa

        vals['ubigeoLlegada'] = guide_id.dst_district_id.code[2:]
        vals['direccionLlegada'] = guide_id.dst_street
        vals['codSucursalLlegada'] = guide_id.dst_branch_id.code
        if partner_id.doc_type == '6':
            vals['rucLlegada'] = partner_id.doc_number
        vehículos = []
        for vehicle_id in guide_id.vehicle_ids:
            vehículos.append({'principal': vehicle_id.is_main, 'placa': vehicle_id.name.replace("-", "")})
        vals['vehículos'] = vehículos
        vals['ubigeoPartida'] = guide_id.src_district_id.code[2:]
        vals['direccionPartida'] = guide_id.src_street
        vals['codSucursalPartida'] = guide_id.src_branch_id.code
        if sender_id.doc_type == '6':
            vals['rucPartida'] = sender_id.doc_number
        vals['detalles'] = self._get_detalles_guia(
            guide_id.line_ids)
        documento = Documento()
        documento.setDocument(vals)
        data = documento.getDocumento(key, crt)
        return data

    def get_eguide_document(self, guide_id):
        data = {}
        key = guide_id.company_id.pe_certificate_id.key
        crt = guide_id.company_id.pe_certificate_id.crt
        data = self._get_eguide_document(guide_id, key, crt)
        return data

    def send_eguide_document(self, guide_id):
        soap = {}
        soap['ruc'] = guide_id.company_id.partner_id.doc_number
        soap['usuario'] = guide_id.company_id.pe_eguide_server_id.user
        soap['clave'] = guide_id.company_id.pe_eguide_server_id.password
        soap['url'] = guide_id.company_id.pe_eguide_server_id.url
        soap['idCliente'] = guide_id.company_id.pe_eguide_server_id.client_id
        soap['claveCliente'] = guide_id.company_id.pe_eguide_server_id.client_secret
        nombre_documento = guide_id.get_document_name()
        xml = guide_id.attachment_id.datas
        documento = Documento()
        data = documento.enviarDocumento(soap, nombre_documento, "guia", xml)
        return data

    def get_document_guide_status(self, cpe_id, tipo):
        documento = Documento()
        soap = {}
        soap['ruc'] = cpe_id.company_id.partner_id.doc_number
        soap['usuario'] = cpe_id.company_id.pe_eguide_server_id.user
        soap['clave'] = cpe_id.company_id.pe_eguide_server_id.password
        soap['url'] = cpe_id.company_id.pe_eguide_server_id.url
        soap['idCliente'] = cpe_id.company_id.pe_eguide_server_id.client_id
        soap['claveCliente'] = cpe_id.company_id.pe_eguide_server_id.client_secret
        nombre_documento = cpe_id.get_document_name()
        ticket = cpe_id.ticket
        data = documento.obtenerEstadoDocumento(soap, nombre_documento, tipo, ticket)
        return data

