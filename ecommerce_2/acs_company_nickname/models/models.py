# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request

class ResCompany(models.Model):
    _inherit = 'res.company'

    nickname = fields.Char(string="Nickname")


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def session_info(self):
        result = super(IrHttp, self).session_info()
        if request.env.user._is_internal():
            for company in request.env.user.company_ids.with_context(bin_size=True):
                result['user_companies']['allowed_companies'][company.id].update({
                    'nickname': company.nickname or company.name,
                })
        return result
