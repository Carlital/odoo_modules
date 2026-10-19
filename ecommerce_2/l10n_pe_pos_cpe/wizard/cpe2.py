from librecpe import Documento
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

class PeCPESend(models.AbstractModel):
    _inherit = "pe.cpe.send"

    def _get_adquirente(self, partner_id):
        res = super()._get_adquirente(partner_id)
        if partner_id.id == self.env.ref('l10n_pe_pos.partner_pe_cf').id:
            res['adquirente']['numDocumento'] = '-'
            res['adquirente']['tipoDocumento'] = '-'
        return res
    
