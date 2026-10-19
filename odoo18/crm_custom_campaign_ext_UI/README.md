# CRM Campaign Manager - UI Enhancement

## Descripción

Módulo de extensión visual para `crm_custom_campaign_ext_CRUD` que proporciona una interfaz mejorada e interactiva para la gestión comercial de campañas y planes.

## Características

### 🎨 Galería Visual Mejorada
- Visualización en tarjetas tipo "pricing table" profesional
- Colores dinámicos según tipo de plan (Diamond, Platinum, Gold, Silver, Bronze, Basic, Starter)
- Diseño responsive con múltiples columnas
- Iconos de redes sociales integrados

### 🎯 Drag & Drop
- Reordenar planes arrastrando las tarjetas
- Actualización automática de secuencias en base de datos
- Feedback visual durante el arrastre
- Handle dedicado para arrastrar (icono grip)

### ⚡ Acciones Rápidas (Hover)
Botones flotantes que aparecen al pasar el mouse sobre cada tarjeta:
- ✏️ **Editar**: Abre el formulario del plan en modal
- 👁️ **Activar/Desactivar**: Toggle del estado activo
- 📋 **Duplicar**: Crea una copia del plan
- 🗑️ **Archivar**: Desactiva el plan

### 🎭 Vista Comercial
- Se integra en la pestaña "Vista comercial (solo lectura)" de Subcampañas
- Muestra todos los planes activos con sus bloques comerciales
- Información de precio con y sin IVA
- Visualización de iconos de apps/redes sociales

## Dependencias

- `crm_custom_campaign_ext`: Módulo base con modelos y CRUD
- `web`: Framework web de Odoo

## Instalación

1. Copiar el módulo a `addons` o `custom_addons`
2. Actualizar lista de aplicaciones
3. Instalar `CRM Campaign Manager - UI Enhancement`

## Estructura

```
crm_custom_campaign_ext_UI/
├── __init__.py
├── __manifest__.py
├── README.md
├── static/
│   └── src/
│       ├── js/
│       │   ├── bc_plan_gallery.js          # Widget selector de planes
│       │   └── bc_subcampaign_gallery.js   # Widget galería interactiva
│       ├── xml/
│       │   └── bc_plan_gallery.xml         # Templates OWL
│       └── css/
│           └── bc_gallery.css              # Estilos visuales
└── views/
    └── bc_subcampaign_views_ui.xml         # Herencia de vistas
```

## Tecnologías

- **OWL (Odoo Web Library)**: Framework de componentes reactivos
- **JavaScript ES6+**: Lógica de interactividad
- **CSS3**: Estilos y animaciones
- **HTML5 Drag & Drop API**: Funcionalidad de arrastre

## Uso

### Vista Comercial en Subcampañas

1. Ir a **CRM → Campañas Personalizadas → Subcampañas (BC)**
2. Abrir una subcampaña
3. Click en la pestaña **"Vista comercial (solo lectura)"**
4. Ver la galería de planes con:
   - Tarjetas visuales de cada plan
   - Arrastrar para reordenar
   - Hover sobre tarjetas para acciones rápidas

### Selector de Planes en Leads

El widget también se usa en el formulario de Leads para seleccionar planes visualmente.

## Permisos

Las acciones de edición están disponibles para:
- Administradores del sistema
- Jefe de Operaciones (grupo definido en `crm_custom_lead`)

## Autor

C2Q

## Licencia

LGPL-3
