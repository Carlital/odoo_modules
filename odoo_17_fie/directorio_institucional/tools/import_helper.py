# -*- coding: utf-8 -*-
"""
Script de ayuda para importar datos al Directorio Institucional

Este script genera un archivo CSV que puede ser importado directamente
en Odoo a través de la interfaz de Contactos.

Formato de entrada (separado por |):
Apellidos y Nombres | Cargo institucional | Unidad a la que pertenece | Teléfono institucional | Extensión telefónica

El script:
1. Lee los datos desde un archivo de texto
2. Genera un CSV compatible con Odoo
3. Incluye la etiqueta "directorio" automáticamente
"""

import csv
import sys

def procesar_linea(linea):
    """Procesa una línea del formato original y retorna un diccionario"""
    partes = [p.strip() for p in linea.split('|')]
    
    if len(partes) != 5:
        return None
    
    return {
        'name': partes[0],
        'x_cargo_institucional': partes[1],
        'x_unidad_pertenece': partes[2],
        'x_telefono_institucional': partes[3],
        'x_extension_telefonica': partes[4],
        'category_id': 'directorio'  # Etiqueta
    }

def generar_csv(archivo_entrada, archivo_salida='directorio_import.csv'):
    """
    Genera un archivo CSV listo para importar en Odoo
    
    :param archivo_entrada: Ruta al archivo con los datos originales
    :param archivo_salida: Ruta del archivo CSV de salida
    """
    contactos = []
    
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                
                # Ignorar líneas vacías o que parecen encabezados
                if not linea or linea.startswith('Apellidos') or linea.startswith('Formato'):
                    continue
                
                contacto = procesar_linea(linea)
                if contacto:
                    contactos.append(contacto)
        
        # Escribir CSV
        if contactos:
            campos = ['name', 'x_cargo_institucional', 'x_unidad_pertenece', 
                     'x_telefono_institucional', 'x_extension_telefonica', 'category_id']
            
            with open(archivo_salida, 'w', newline='', encoding='utf-utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                writer.writerows(contactos)
            
            print(f"✓ Archivo CSV generado exitosamente: {archivo_salida}")
            print(f"✓ Total de contactos procesados: {len(contactos)}")
            print(f"\nPasos siguientes:")
            print(f"1. Ir a Odoo > Contactos")
            print(f"2. Crear la etiqueta 'directorio' si no existe")
            print(f"3. Click en Favoritos > Importar registros")
            print(f"4. Seleccionar el archivo: {archivo_salida}")
            print(f"5. Mapear columnas (debería ser automático)")
            print(f"6. Importar")
        else:
            print("⚠ No se encontraron datos válidos para procesar")
            
    except FileNotFoundError:
        print(f"✗ Error: No se encontró el archivo {archivo_entrada}")
    except Exception as e:
        print(f"✗ Error al procesar: {e}")


def mostrar_ejemplo():
    """Muestra un ejemplo de uso"""
    print("=" * 70)
    print("GENERADOR DE CSV PARA DIRECTORIO INSTITUCIONAL")
    print("=" * 70)
    print("\nFormato del archivo de entrada (separado por |):")
    print("Apellidos y Nombres | Cargo | Unidad | Teléfono | Extensión\n")
    print("Ejemplo:")
    print("Vaca Barahona Byron Ernesto | Rectorado | Rectorado | 593(03) 2998-200 | 1001\n")
    print("Uso:")
    print("  python import_helper.py archivo_datos.txt")
    print("  python import_helper.py archivo_datos.txt salida.csv")
    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        mostrar_ejemplo()
    else:
        archivo_entrada = sys.argv[1]
        archivo_salida = sys.argv[2] if len(sys.argv) > 2 else 'directorio_import.csv'
        generar_csv(archivo_entrada, archivo_salida)
