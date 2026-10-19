import logging

_logger = logging.getLogger(__name__)

# importar subpaquetes para que Odoo cargue los modelos, wizards y controllers
from . import models
from . import wizards
from . import controllers

# importar el módulo que contiene la implementación real del hook
from .models import n8n_config as _n8n_config

def post_init_hook(env):
    """
    Odoo calls post_init_hook(env). Delegate to the implementation in
    models.n8n_config which expects (cr, registry).
    """
    try:
        return _n8n_config.post_init_hook(env.cr, env.registry)
    except Exception as e:
        _logger.exception('post_init_hook delegation failed: %s', e)
        return None