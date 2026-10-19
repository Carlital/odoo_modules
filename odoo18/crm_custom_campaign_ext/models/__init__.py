from . import bc_models
from . import campaign_ext
from . import bc_attribute
from . import bc_lead_inherit
import logging

_logger = logging.getLogger(__name__)

# Lista de submódulos de models que deben importarse.
# Añade aquí otros nombres de archivos .py que tengas dentro de models/ si es necesario.
_submodules = [
    'n8n_config',
    # 'otro_modelo', ...
]

for _mod in _submodules:
    try:
        __import__(f'odoo.addons.crm_custom_campaign_ext.models.{_mod}', fromlist=['*'])
    except Exception:
        _logger.exception('Error importing models.%s (ignored during init to avoid circular import)', _mod)
