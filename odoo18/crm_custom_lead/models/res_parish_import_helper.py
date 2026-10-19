from odoo import models, fields, api


class ResParishImportHelper(models.Model):
    _inherit = 'res.parish'

    # Campos auxiliares para importación con el importador estándar.
    city_name_import = fields.Char(
        string='Ciudad (Import)',
        compute='_compute_city_name_import',
        inverse='_inverse_city_name_import',
        help='Solo importación: al escribir, crea/establece la ciudad usando el nombre y la provincia.',
    )

    state_name_import = fields.Char(
        string='Provincia (Import)',
        compute='_compute_state_name_import',
        inverse='_inverse_state_name_import',
        help='Solo importación: al escribir, crea/establece la provincia usando el nombre y el país.',
    )

    def _compute_city_name_import(self):
        for rec in self:
            rec.city_name_import = rec.city_id.name if rec.city_id else False

    def _inverse_city_name_import(self):
        City = self.env['res.city']
        for rec in self:
            name = (rec.city_name_import or '').strip()
            if rec.city_id or not name:
                continue
            # Asegurar que exista la provincia
            if not rec.state_id:
                self._ensure_state_for_rec(rec)
            state = rec.state_id
            if not state:
                # Sin provincia no se puede crear ciudad
                continue
            city = City.search([('name', '=', name), ('state_id', '=', state.id)], limit=1)
            if not city:
                city = City.create({
                    'name': name,
                    'state_id': state.id,
                    'country_id': state.country_id.id,
                })
            rec.city_id = city.id

    def _compute_state_name_import(self):
        for rec in self:
            rec.state_name_import = rec.state_id.name if rec.state_id else False

    def _inverse_state_name_import(self):
        for rec in self:
            if rec.state_id:
                continue
            self._ensure_state_for_rec(rec)

    def _ensure_state_for_rec(self, rec):
        """Garantiza la provincia"""
        State = self.env['res.country.state']
        country = rec.country_id or self.env['res.country'].search([('code', '=', 'EC')], limit=1)
        state_name = (rec.state_name_import or '').strip()
        if not (state_name and country):
            return
        state = State.search([('name', '=', state_name), ('country_id', '=', country.id)], limit=1)
        if not state:
            code = self._generate_state_code(state_name, country)
            state = State.create({
                'name': state_name,
                'code': code,
                'country_id': country.id,
            })
        rec.state_id = state.id

    def _generate_state_code(self, name, country):
        import re
        parts = [p for p in re.split(r"\W+", name.upper()) if p]
        if len(parts) == 1:
            base = parts[0][:3]
        else:
            base = ''.join(p[0] for p in parts)[:4]
        if not base:
            base = 'ST'
        State = self.env['res.country.state']
        code = base
        i = 1
        while State.search([('code', '=', code), ('country_id', '=', country.id)], limit=1):
            i += 1
            code = f"{base}{i}"
        return code

    def _prepare_state_city_from_import_vals(self, vals):
        country = None
        country_id = vals.get('country_id')
        if country_id:
            country = self.env['res.country'].browse(country_id)
        if not country:
            country = self.env['res.country'].search([('code', '=', 'EC')], limit=1)

        # Estado por nombre (state_id)
        state_id = vals.get('state_id')
        st_name = (vals.get('state_name_import') or '').strip()
        if not state_id and st_name:
            state = self.env['res.country.state'].search([('name', '=', st_name), ('country_id', '=', country.id)], limit=1)
            if not state:
                code = self._generate_state_code(st_name, country)
                state = self.env['res.country.state'].create({'name': st_name, 'code': code, 'country_id': country.id})
            vals['state_id'] = state.id
            state_id = state.id

        # Ciudad por nombre (city_id)
        ct_name = (vals.get('city_name_import') or '').strip()
        if not vals.get('city_id') and ct_name and state_id:
            city = self.env['res.city'].search([('name', '=', ct_name), ('state_id', '=', state_id)], limit=1)
            if not city:
                state = self.env['res.country.state'].browse(state_id)
                city = self.env['res.city'].create({'name': ct_name, 'state_id': state_id, 'country_id': state.country_id.id})
            vals['city_id'] = city.id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        results = self.browse()
        for vals in vals_list:
            vals = self._prepare_state_city_from_import_vals(dict(vals))
            name = (vals.get('name') or '').strip()
            city_id = vals.get('city_id')
            if name and city_id:
                existing = self.env['res.parish'].search([
                    ('name', '=', name), ('city_id', '=', city_id)
                ], limit=1)
                if existing:
                    # No tocar registros existentes
                    results |= existing
                    continue
            results |= super().create([vals])
        return results

    def write(self, vals):
        vals = self._prepare_state_city_from_import_vals(dict(vals))
        return super().write(vals)
