# GUÍA DE INSTALACIÓN Y USO - DIRECTORIO INSTITUCIONAL

## 📋 Descripción

Módulo de Odoo 17 para gestionar y mostrar el directorio telefónico institucional en el sitio web, sin imágenes, con filtros por unidad y búsqueda por nombre.

## 🚀 Instalación

### 1. Copiar el módulo
Copiar la carpeta `directorio_institucional` al directorio de addons de Odoo.

### 2. Actualizar lista de aplicaciones
```bash
# En Odoo, ir a:
Aplicaciones > Actualizar lista de aplicaciones
```

### 3. Instalar el módulo
```bash
# Buscar "Directorio Institucional" e instalar
```

## 📥 Importar Datos

### Opción 1: Crear la etiqueta "directorio" manualmente

1. Ir a **Contactos > Configuración > Etiquetas de Contacto**
2. Crear nueva etiqueta con nombre: **directorio**
3. Guardar

### Opción 2: Importar contactos desde CSV

#### Paso 1: Preparar los datos
Los datos deben estar en formato:
```
Apellidos y Nombres | Cargo institucional | Unidad | Teléfono | Extensión
```

Ejemplo:
```
Vaca Barahona Byron Ernesto | Rectorado | Rectorado | 593(03) 2998-200 | 1001
```

#### Paso 2: Generar CSV (opcional)
Si tienes un archivo de texto con los datos:

```bash
cd directorio_institucional/tools
python import_helper.py datos_ejemplo.txt directorio.csv
```

#### Paso 3: Importar en Odoo

1. Ir a **Contactos**
2. Asegurarse de que existe la etiqueta "directorio"
3. Click en **Favoritos > Importar registros**
4. Seleccionar el archivo CSV
5. Mapear las columnas:
   - `name` → Nombre
   - `x_cargo_institucional` → Cargo Institucional
   - `x_unidad_pertenece` → Unidad a la que Pertenece
   - `x_telefono_institucional` → Teléfono Institucional
   - `x_extension_telefonica` → Extensión Telefónica
   - `category_id` → Etiquetas (debe contener "directorio")
6. Click en **Importar**

### Opción 3: Crear contactos manualmente

1. Ir a **Contactos > Crear**
2. Llenar los campos:
   - **Nombre**: Apellidos y Nombres
   - **Etiquetas**: Agregar "directorio"
   - En la pestaña **Directorio Institucional**:
     - Cargo Institucional
     - Unidad a la que Pertenece
     - Teléfono Institucional
     - Extensión Telefónica
3. Guardar

## 🌐 Agregar el Snippet al Sitio Web

1. Ir a **Sitio Web > Editar**
2. En el editor, click en **Bloques > Estructura**
3. Arrastrar el bloque **"Directorio Institucional"** a la página
4. Guardar cambios

El snippet incluye:
- ✅ Búsqueda por nombre o apellido
- ✅ Filtro por unidad institucional
- ✅ Paginación automática
- ✅ Diseño responsive
- ✅ Sin imágenes (solo datos de contacto)

## 📊 Estructura de Datos

Cada contacto del directorio contiene:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Nombre | Apellidos y nombres completos | Vaca Barahona Byron Ernesto |
| Cargo Institucional | Puesto que ocupa | Rectorado |
| Unidad | Departamento/Facultad | Rectorado |
| Teléfono Institucional | Número completo | 593(03) 2998-200 |
| Extensión Telefónica | Extensión interna | 1001 |
| Email | Correo electrónico (opcional) | rector@espoch.edu.ec |

## 🎨 Personalización

### Cambiar colores
Editar el archivo: `static/src/css/directorio.css`

Variables principales:
```css
/* Color primario (azul) */
#3498db → Cambiar al color deseado

/* Color secundario (azul oscuro) */
#2980b9 → Cambiar al color deseado
```

### Cambiar cantidad de resultados por página
Editar: `static/src/js/directorio.js`

```javascript
start: function () {
    this.limit = 12; // Cambiar este número
    ...
}
```

### Modificar el diseño del snippet
Editar: `views/snippets_templates.xml`

## 🔧 Troubleshooting

### No aparece la pestaña "Directorio Institucional"
- Asegúrate de que el contacto tiene la etiqueta "directorio"
- La pestaña solo aparece si `x_es_directorio = True`

### El filtro de unidades está vacío
- Verifica que los contactos tengan el campo "Unidad a la que Pertenece" completado
- Asegúrate de que tienen la etiqueta "directorio"

### El snippet no carga datos
- Verifica que el módulo esté correctamente instalado
- Revisa los logs de Odoo para errores
- Confirma que existen contactos con la etiqueta "directorio"

### Error al importar CSV
- Verifica que el archivo esté en formato UTF-8
- Confirma que la etiqueta "directorio" existe antes de importar
- Revisa que las columnas estén correctamente mapeadas

## 📝 Notas Importantes

1. **Etiqueta obligatoria**: Todos los contactos del directorio DEBEN tener la etiqueta "directorio"
2. **Campos personalizados**: Los campos con prefijo `x_` son personalizados de este módulo
3. **Permisos**: El snippet es público (no requiere login)
4. **Caché**: Después de cambios en CSS/JS, limpiar caché del navegador

## 📞 Soporte

Para problemas o consultas sobre este módulo, contactar al equipo de desarrollo de la ESPOCH.

## 📄 Licencia

LGPL-3
