# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrEmployeeCategory(models.Model):
    _inherit = 'hr.employee.category'
    
    is_motorizado = fields.Boolean(string="Es Motorizado", default=False)
    
    @api.model
    def _setup_motorizado_category(self):
        """Asegura que exista la categoría Motorizado con is_motorizado=True"""
        cat_motorizado = self.search([('name', '=', 'Motorizado')], limit=1)
        if cat_motorizado and not cat_motorizado.is_motorizado:
            cat_motorizado.write({'is_motorizado': True})
        elif not cat_motorizado:
            self.create({'name': 'Motorizado', 'is_motorizado': True})
        return True


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    es_motorizado = fields.Boolean(
        string="Es Motorizado", 
        compute="_compute_es_motorizado",
        store=True
    )
    es_motorizado_manual = fields.Boolean(string="Marcar como Motorizado", default=False)
    telefono_motorizado = fields.Char(string="Teléfono Motorizado")
    cedula_motorizado = fields.Char(string="Cédula Motorizado")
    
    @api.depends('category_ids', 'category_ids.is_motorizado')
    def _compute_es_motorizado(self):
        for rec in self:
            rec.es_motorizado = any(cat.is_motorizado for cat in rec.category_ids)
    
    @api.model
    def _recompute_es_motorizado(self):
        """Recomputa el campo es_motorizado para todos los empleados"""
        employees = self.search([])
        employees._compute_es_motorizado()
        return True
    
    @api.model_create_multi
    def create(self, vals_list):
        """Asigna automáticamente la categoría Motorizado si se marca."""
        for vals in vals_list:
            if vals.get('es_motorizado_manual'):
                # Buscar o crear la categoría "Motorizado"
                cat_motorizado = self.env['hr.employee.category'].search([
                    ('is_motorizado', '=', True)
                ], limit=1)
                
                if not cat_motorizado:
                    cat_motorizado = self.env['hr.employee.category'].sudo().create({
                        'name': 'Motorizado',
                        'is_motorizado': True,
                    })
                
                # Buscar o crear el departamento "Motorizados"
                dept_motorizado = self.env['hr.department'].sudo().search([
                    ('name', '=', 'Motorizados')
                ], limit=1)
                
                if not dept_motorizado:
                    dept_motorizado = self.env['hr.department'].sudo().create({
                        'name': 'Motorizados',
                    })
                
                # Asignar la categoría
                if 'category_ids' in vals:
                    # Si category_ids es una lista de tuplas, agregar la nueva categoría
                    if isinstance(vals['category_ids'], list):
                        vals['category_ids'].append((4, cat_motorizado.id))
                else:
                    vals['category_ids'] = [(4, cat_motorizado.id)]
                
                # Asignar el departamento
                vals['department_id'] = dept_motorizado.id
                
                # Limpiar campos no deseados para motorizado
                # Solo dejamos: name, category_ids, department_id, telefono_motorizado, cedula_motorizado
                campos_permitidos = {
                    'name', 'category_ids', 'department_id', 'telefono_motorizado', 
                    'cedula_motorizado', 'company_id', 'es_motorizado_manual'
                }
                
                # Crear diccionario limpio solo con campos permitidos
                vals_limpios = {k: v for k, v in vals.items() if k in campos_permitidos}
                
                # Asegurar que no se asigne usuario (sin acceso al sistema)
                vals_limpios['user_id'] = False
                
                # Limpiar campos de teléfono/contacto que no se deben usar
                vals_limpios['work_phone'] = False
                vals_limpios['mobile_phone'] = False
                vals_limpios['phone'] = False
                vals_limpios['work_email'] = False
                
                # Reemplazar vals con la versión limpia
                vals.clear()
                vals.update(vals_limpios)
                
                # Eliminar el campo temporal después de procesar
                if 'es_motorizado_manual' in vals:
                    del vals['es_motorizado_manual']
        
        return super().create(vals_list)
    
    @api.model
    def crear_motorizado(self, nombre, telefono=False, cedula=False):
        """
        Crea un empleado tipo motorizado sin usuario del sistema.
        
        Args:
            nombre (str): Nombre del motorizado
            telefono (str, optional): Teléfono del motorizado
            cedula (str, optional): Cédula del motorizado
        
        Returns:
            hr.employee: Registro del empleado motorizado creado
        """
        # Buscar o crear la categoría "Motorizado"
        cat_motorizado = self.env['hr.employee.category'].search([
            ('is_motorizado', '=', True)
        ], limit=1)
        
        if not cat_motorizado:
            cat_motorizado = self.env['hr.employee.category'].sudo().create({
                'name': 'Motorizado',
                'is_motorizado': True,
            })
        
        # Buscar o crear el departamento "Motorizados"
        dept_motorizado = self.env['hr.department'].sudo().search([
            ('name', '=', 'Motorizados')
        ], limit=1)
        
        if not dept_motorizado:
            dept_motorizado = self.env['hr.department'].sudo().create({
                'name': 'Motorizados',
            })
        
        # Verificar si ya existe un motorizado con ese nombre
        motorizado_existente = self.search([
            ('name', '=', nombre),
            ('es_motorizado', '=', True)
        ], limit=1)
        
        if motorizado_existente:
            # Actualizar información si es necesario
            vals_update = {}
            if telefono and not motorizado_existente.telefono_motorizado:
                vals_update['telefono_motorizado'] = telefono
            if cedula and not motorizado_existente.cedula_motorizado:
                vals_update['cedula_motorizado'] = cedula
            if not motorizado_existente.department_id:
                vals_update['department_id'] = dept_motorizado.id
            if vals_update:
                motorizado_existente.write(vals_update)
            return motorizado_existente
        
        # Crear nuevo empleado motorizado (sin user_id = sin acceso al sistema)
        vals = {
            'name': nombre,
            'category_ids': [(6, 0, [cat_motorizado.id])],
            'department_id': dept_motorizado.id,
            'telefono_motorizado': telefono or '',
            'cedula_motorizado': cedula or '',
            'company_id': self.env.user.company_id.id if self.env.user.company_id else False,
            # NO se asigna user_id, por lo tanto no tiene acceso al sistema
        }
        
        motorizado = self.sudo().create(vals)
        return motorizado
