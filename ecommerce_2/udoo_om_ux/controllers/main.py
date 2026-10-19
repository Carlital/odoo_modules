# -*- coding: utf-8 -*-
# Copyright 2024 Sveltware Solutions

import base64
import io

try:
    from werkzeug.utils import send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file

import odoo
from odoo import _, http
from odoo.http import request, Response
from odoo.tools import file_path
from odoo.tools.mimetypes import guess_mimetype

from odoo.addons.web.controllers.binary import Binary


class OmuxBinary(Binary):
    @http.route(
        [
            '/uilogo',
        ],
        type='http',
        auth='none',
        cors='*',
    )
    def company_uilogo(self, dbname=None, **kw):
        imgname = 'logo'
        imgext = '.png'
        dbname = request.db
        uid = (request.session.uid if dbname else None) or odoo.SUPERUSER_ID

        if not dbname:
            return self.company_logo(dbname, **kw)
        else:
            try:
                # create an empty registry
                registry = odoo.modules.registry.Registry(dbname)

                with registry.cursor() as cr:
                    company = int(kw['company']) if kw and kw.get('company') else False
                    flogo = 'logo_lui' if request.httprequest.cookies.get('color_scheme') == 'dark' else 'logo_dui'

                    if company:
                        cr.execute(
                            f'SELECT {flogo}, write_date FROM res_company WHERE id = %s',
                            (company,),
                        )
                    else:
                        cr.execute(
                            f'SELECT c.{flogo}, c.write_date FROM res_users u LEFT JOIN res_company c ON c.id = u.company_id WHERE u.id = %s',
                            (uid,),
                        )
                    row = cr.fetchone()
                    if row and row[0]:
                        image_base64 = base64.b64decode(row[0])
                        image_data = io.BytesIO(image_base64)
                        mimetype = guess_mimetype(image_base64, default='image/png')
                        imgext = '.' + mimetype.split('/')[1]
                        if imgext == '.svg+xml':
                            imgext = '.svg'
                        response = send_file(
                            image_data,
                            request.httprequest.environ,
                            download_name=imgname + imgext,
                            mimetype=mimetype,
                            last_modified=row[1],
                            response_class=Response,
                        )
                    else:
                        return self.company_logo(dbname, **kw)
            except Exception:
                response = http.Stream.from_path(file_path(f'web/static/img/{imgname}{imgext}')).get_response()

        return response