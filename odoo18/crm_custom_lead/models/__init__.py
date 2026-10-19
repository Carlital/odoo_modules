from . import res_parish              # 1) definir el modelo base
from . import res_city_ext
from . import res_groups
from . import crm_campaign
from . import hr_employee_motorizado
from . import res_users
from . import crm_lead                # 2) el lead puede referenciar res.parish
from . import res_parish_import_helper  # 3) helpers/extensiones que heredan de res.parish
