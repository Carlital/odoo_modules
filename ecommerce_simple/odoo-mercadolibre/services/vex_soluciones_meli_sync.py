import requests
from odoo import api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

def sync_meli_options(env, site_id, access_token, instance):
    _logger.info(f"[ML-SYNC] Iniciando sincronización de opciones para site_id={site_id}, instancia={instance}")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Sync listing_type
    try:
        url = f"https://api.mercadolibre.com/sites/{site_id}/listing_types"
        r = requests.get(url, headers=headers)
        if r.ok:
            existing_options = env['meli.option'].sudo().search([
                ('instance_id', '=', instance),
                ('field_name', '=', 'listing_type'),
                ('site_id', '=', site_id)
            ])
            existing_names = set(existing_options.mapped('name'))
            existing_codes = set(existing_options.mapped('code'))
            count = 0
            for lt in r.json():
                if lt['name'] not in existing_names and lt['id'] not in existing_codes:
                    env['meli.option'].sudo().create({
                        'name': lt['name'],
                        'code': lt['id'],
                        'field_name': 'listing_type',
                        'site_id': site_id,
                        'instance_id': instance
                    })
                    count += 1
            _logger.info(f"[ML-SYNC] listing_types sincronizados: {count}")
    except Exception as e:
        _logger.error(f"[ML-SYNC] Error al sincronizar listing_types: {str(e)}")
    
    # Obtener una categoría para extraer condiciones
    try:
        #cats = requests.get(f"https://api.mercadolibre.com/sites/{site_id}/categories", headers=headers).json()
        cats = env['vex.category'].sudo().search([
                ('instance_id', '=', instance),
                #('parent_id', '=', False),
                ('site_id', '=', site_id)
            ])
        if cats:
            sample_cat_id = cats[0]['codigo_ml']
            attrs = requests.get(f"https://api.mercadolibre.com/categories/{sample_cat_id}/attributes", headers=headers).json()
            for attr in attrs:
                if attr['id'] == 'ITEM_CONDITION':
                    existing_options = env['meli.option'].sudo().search([
                        ('instance_id', '=', instance),
                        ('field_name', '=', 'condition'),
                        ('site_id', '=', site_id)
                    ])
                    existing_names = set(existing_options.mapped('name'))
                    existing_codes = set(existing_options.mapped('code'))
                    count = 0
                    for value in attr['values']:
                        if value['name'] not in existing_names and value['id'] not in existing_codes:
                            env['meli.option'].sudo().create({
                                'name': value['name'],
                                'code': value['id'],
                                'field_name': 'condition',
                                'site_id': site_id,
                                'instance_id': instance
                            })
                            count += 1
                    _logger.info(f"[ML-SYNC] condiciones sincronizadas: {count}")
    except Exception as e:
        _logger.error(f"[ML-SYNC] Error al sincronizar condition: {str(e)}")

    # Buying mode fijo
    try:
        existing_options = env['meli.option'].sudo().search([
            ('instance_id', '=', instance),
            ('field_name', '=', 'buying_mode'),
            ('site_id', '=', site_id)
        ])
        existing_names = set(existing_options.mapped('name'))
        existing_codes = set(existing_options.mapped('code'))
        count = 0
        for bm in ['buy_it_now', 'auction']:
            if bm.replace('_', ' ').capitalize() not in existing_names and bm not in existing_codes:
                env['meli.option'].sudo().create({
                    'name': bm.replace('_', ' ').capitalize(),
                    'code': bm,
                    'field_name': 'buying_mode',
                    'site_id': site_id,
                    'instance_id': instance
                })
                count += 1
        _logger.info(f"[ML-SYNC] buying_modes sincronizados: {count}")
    except Exception as e:
        _logger.error(f"[ML-SYNC] Error al crear buying_modes: {str(e)}")


def sync_meli_categories(env, site_id, access_token, instance):
    _logger.info(f"[ML-SYNC] Iniciando sincronización de categorías para site_id={site_id}, instancia={instance}")
    headers = {"Authorization": f"Bearer {access_token}"}

    def create_category_tree(cat_data, parent=False):
        try:
            existing_cat = env['meli.category'].sudo().search([
                ('meli_id', '=', cat_data['id']),
                ('site_id', '=', site_id),
                ('instance_id', '=', instance)
            ], limit=1)
            
            if existing_cat:
                _logger.debug(f"[ML-SYNC] Categoría ya existente: {cat_data['name']} ({cat_data['id']})")
                cat = existing_cat
            else:
                cat = env['meli.category'].sudo().create({
                    'name': cat_data['name'],
                    'meli_id': cat_data['id'],
                    'parent_id': parent.id if parent else False,
                    'site_id': site_id,
                    'full_path': (parent.full_path + ' / ' if parent else '') + cat_data['name'],
                    'instance_id': instance
                })
                _logger.debug(f"[ML-SYNC] Categoría creada: {cat_data['name']} ({cat_data['id']})")
            
            for child in cat_data.get('children_categories', []):
                try:
                    child_data = requests.get(f"https://api.mercadolibre.com/categories/{child['id']}", headers=headers).json()
                    create_category_tree(child_data, cat)
                except Exception as e:
                    _logger.warning(f"[ML-SYNC] Error al obtener categoría hija {child['id']}: {str(e)}")
        except Exception as e:
            _logger.error(f"[ML-SYNC] Error al crear categoría {cat_data.get('name')}: {str(e)}")

    try:
        cats = requests.get(f"https://api.mercadolibre.com/sites/{site_id}/categories", headers=headers).json()
        for cat in cats:
            try:
                cat_data = requests.get(f"https://api.mercadolibre.com/categories/{cat['id']}", headers=headers).json()
                create_category_tree(cat_data)
            except Exception as e:
                _logger.warning(f"[ML-SYNC] Error al obtener detalles de categoría {cat['id']}: {str(e)}")
        _logger.info("[ML-SYNC] Sincronización de categorías finalizada.")
    except Exception as e:
        _logger.error(f"[ML-SYNC] Error al sincronizar categorías: {str(e)}")
