# ACS Products Sales Units Alterns

Módulo para Odoo 18 que permite la conversión automática de productos comprados en unidades de peso (kg, toneladas) a unidades de longitud (metros lineales) mediante pickings automáticos que respetan los flujos nativos de Odoo.

## Características

### Configuración de Productos
- **Campo "Convertible a Metros"**: Checkbox para activar la funcionalidad de conversión
- **Ratio de Conversión**: Cantidad de peso equivalente a 1 metro lineal (ej: 3.0 = 3kg por metro)
- **Producto Contraparte**: Selección del producto equivalente en metros
- **Stock en Metros**: Campo calculado que muestra el stock actual convertido a metros (informativo)

### Proceso de Conversión
1. **Recepción Original**: Se recibe el producto en unidades de peso (kg)
2. **Botón "Convertir"**: Aparece en pickings de recepción validados con productos convertibles
3. **Picking de Salida**: Se genera automáticamente para dar salida al stock en peso y se valida automáticamente
4. **Picking de Recepción**: Se genera para recibir el producto equivalente en metros, requiere validación manual

### Funcionalidades Adicionales
- **Trazabilidad Completa**: Todos los movimientos quedan registrados
- **Validaciones**: Controla que los productos tengan configuración completa
- **Navegación**: Botones para ver los pickings generados en la conversión
- **Reportes**: Vistas específicas para productos convertibles y recepciones pendientes

## Instalación

1. Copiar el módulo en el directorio de addons de Odoo
2. Actualizar la lista de módulos
3. Instalar el módulo "ACS Products Sales Units Alterns"

## Configuración

### 1. Configurar Productos
1. Ir a **Inventario > Productos > Productos**
2. Abrir un producto que se compre en peso
3. En la pestaña **Inventario**, activar "Convertible a Metros"
4. Configurar el "Ratio de Conversión" (ej: 3.0 para 3kg = 1 metro)
5. Seleccionar el "Producto Contraparte (Metros)"

### 2. Crear Productos Contraparte
- Crear productos equivalentes con unidades de medida en metros
- Ejemplo: "Alucim (Kg)" → "Alucim (Mt)"

## Uso

### Conversión de Productos
1. Recibir productos normalmente a través de órdenes de compra o recepciones directas
2. Validar la recepción
3. Hacer clic en el botón **"Convertir"** que apar