# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class DirectorioInstitucionalController(http.Controller):

    @http.route('/directorio_institucional/filtrar', type='json', auth='public', website=True)
    def filtrar_directorio(self, unidad=None, nombre=None, page=1, limit=12):
        """
        Filtra y retorna contactos del directorio institucional
        
        :param unidad: Filtrar por unidad institucional
        :param nombre: Buscar por nombre o apellido
        :param page: Número de página para paginación
        :param limit: Cantidad de resultados por página
        :return: dict con HTML de resultados y paginación
        """
        try:
            # Buscar la etiqueta "directorio"
            directorio_tag = request.env['res.partner.category'].sudo().search([
                ('name', '=ilike', 'directorio')
            ], limit=1)
            
            if not directorio_tag:
                return {
                    'html': '<div class="alert alert-warning">No se encontró la etiqueta "directorio"</div>',
                    'pagination': ''
                }

            # Construir dominio de búsqueda
            domain = [
                ('category_id', 'in', [directorio_tag.id]),
            ]
            
            offset = (int(page) - 1) * limit

            # Filtrar por unidad si se proporciona
            if unidad:
                domain.append(('x_unidad_pertenece', '=', unidad))

            # Buscar por nombre si se proporciona
            if nombre:
                domain.append(('name', 'ilike', nombre))

            # Ejecutar búsqueda
            total_contactos = request.env['res.partner'].sudo().search_count(domain)
            contactos = request.env['res.partner'].sudo().search(
                domain,
                offset=offset,
                limit=limit,
                order='name asc'
            )

            # Generar HTML de resultados
            html_resultado = self._generar_html_contactos(contactos)

            # Generar paginación
            pagination_html = self._generar_paginacion(total_contactos, limit, page)

            return {
                'html': html_resultado,
                'pagination': pagination_html
            }

        except Exception as e:
            _logger.error(f"Error al filtrar directorio: {e}")
            return {
                'html': '<div class="alert alert-danger">Error al cargar el directorio</div>',
                'pagination': ''
            }

    def _generar_html_contactos(self, contactos):
        """Genera el HTML para mostrar los contactos"""
        if not contactos:
            return '''
                <div class="col-12">
                    <div class="directorio-no-results">
                        <i class="fa fa-address-book fa-3x text-muted mb-3"></i>
                        <h5 class="mt-3">No se encontraron contactos</h5>
                        <p class="text-muted">Intenta ajustar los filtros de búsqueda</p>
                    </div>
                </div>
            '''

        html = ''
        for contacto in contactos:
            nombre = contacto.name or 'Sin nombre'
            cargo = contacto.x_cargo_institucional or 'Sin cargo'
            unidad = contacto.x_unidad_pertenece or 'Sin unidad'
            telefono = contacto.x_telefono_institucional or 'Sin teléfono'
            extension = contacto.x_extension_telefonica or 'N/A'
            email = contacto.email or 'Sin correo'

            html += f'''
                <div class="col-12">
                    <div class="directorio-item">
                        <div class="directorio-content">
                            <div class="directorio-header">
                                <h5 class="directorio-nombre">
                                    <i class="fa fa-user-circle me-2"></i>
                                    {nombre}
                                </h5>
                                <span class="directorio-badge">{cargo}</span>
                            </div>
                            
                            <div class="directorio-info">
                                <div class="directorio-info-item">
                                    <i class="fa fa-building"></i>
                                    <span><strong>Unidad:</strong> {unidad}</span>
                                </div>
                                <div class="directorio-info-item">
                                    <i class="fa fa-phone"></i>
                                    <span><strong>Teléfono:</strong> {telefono}</span>
                                </div>
                                <div class="directorio-info-item">
                                    <i class="fa fa-hashtag"></i>
                                    <span><strong>Extensión:</strong> {extension}</span>
                                </div>
                                <div class="directorio-info-item">
                                    <i class="fa fa-envelope"></i>
                                    <span><strong>Email:</strong> {email}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            '''

        return html

    def _generar_paginacion(self, total, limit, current_page):
        """Genera el HTML de paginación"""
        if total <= limit:
            return ''

        total_pages = -(-total // limit)  # Ceiling division
        current_page = int(current_page)

        html = '<ul class="pagination justify-content-center">'

        # Botón anterior
        disabled_prev = ' disabled' if current_page <= 1 else ''
        html += f'''
            <li class="page-item{disabled_prev}">
                <a class="page-link directorio-page" href="#" data-page="{max(1, current_page - 1)}">
                    <i class="fa fa-chevron-left"></i> Anterior
                </a>
            </li>
        '''

        # Páginas
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)

        if start_page > 1:
            html += f'<li class="page-item"><a class="page-link directorio-page" href="#" data-page="1">1</a></li>'
            if start_page > 2:
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>'

        for p in range(start_page, end_page + 1):
            active = ' active' if p == current_page else ''
            html += f'<li class="page-item{active}"><a class="page-link directorio-page" href="#" data-page="{p}">{p}</a></li>'

        if end_page < total_pages:
            if end_page < total_pages - 1:
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>'
            html += f'<li class="page-item"><a class="page-link directorio-page" href="#" data-page="{total_pages}">{total_pages}</a></li>'

        # Botón siguiente
        disabled_next = ' disabled' if current_page >= total_pages else ''
        html += f'''
            <li class="page-item{disabled_next}">
                <a class="page-link directorio-page" href="#" data-page="{min(total_pages, current_page + 1)}">
                    Siguiente <i class="fa fa-chevron-right"></i>
                </a>
            </li>
        '''

        html += '</ul>'
        return html

    @http.route('/directorio_institucional/unidades', type='json', auth='public', website=True)
    def obtener_unidades(self):
        """Obtiene todas las unidades disponibles en el directorio"""
        try:
            unidades = request.env['res.partner'].sudo().get_unidades_directorio()
            return {'unidades': unidades}
        except Exception as e:
            _logger.error(f"Error al obtener unidades: {e}")
            return {'unidades': []}
