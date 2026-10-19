# SUNAT Tables & Catalogs (Peru)

## Overview
This module provides a comprehensive set of SUNAT (Superintendencia Nacional de Aduanas y de Administración Tributaria) catalogs and tables required for compliant electronic invoicing and accounting in Peru. It serves as a foundational data module for other Peruvian localization modules (e.g., `l10n_pe_edi`).

## Included Catalogs
The module loads and manages the following SUNAT Catalogs (Anexos):

*   **Catalog 01:** Document Types (Tipo de Documento)
*   **Catalog 02:** Currency Codes (Tipo de Monedas)
*   **Catalog 03:** Unit of Measure (Unidad de Medida Comercial)
*   **Catalog 04:** Country Codes (Código de País)
*   **Catalog 05:** Tax Types (Tipos de Tributos)
*   **Catalog 06:** Identity Document Types (Tipo de Documento de Identidad)
*   **Catalog 07:** IGV Type (Tipo de Afectación del IGV)
*   **Catalog 08:** ISC Calculation System (Sistema de Cálculo del ISC)
*   **Catalog 09:** Credit Note Types (Tipo de Nota de Crédito)
*   **Catalog 10:** Debit Note Types (Tipo de Nota de Débito)
*   **Catalog 11:** Summary Value Types (Tipo de valor de venta)
*   **Catalog 12:** Related Documents (Documentos Relacionados)
*   **Catalog 13:** (Missing in list, check code)
*   **Catalog 14:** Other Tax Concepts (Otros conceptos tributarios)
*   **Catalog 15:** Additional Elements (Elementos Adicionales)
*   **Catalog 16:** Unit Price Type (Tipo de precio de venta unitario)
*   **Catalog 17:** Operation Types (Tipo de Operación)
*   **Catalog 18:** Transport Modality (Modalidad de transporte)
*   **Catalog 19:** Item State (Estado del ítem)
*   **Catalog 20:** Transfer Reason (Motivo de traslado)
*   **Catalog 21:** Related Documents GRE (Documentos relacionados GRE)
*   **Catalog 22:** Perceptions Regime (Regimen de percepciones)
*   **Catalog 23:** Retentions Regime (Regimen de retenciones)
*   **Catalog 24:** Public Services Tariff (Tarifa de servicios públicos)
*   **Catalog 26:** Loan Type (Tipo de préstamo)
*   **Catalog 27:** First Housing Indicator (Indicador de primera vivienda)
*   **Catalog 51:** Operation Types (Tipo de Operación - Code 51)
*   **Catalog 52:** Legends (Leyendas)
*   **Catalog 53:** Charges/Discounts (Cargos o Descuentos)
*   **Catalog 54:** Detractions (Bienes y Servicios sujetos a Detracciones)
*   **Catalog 55:** Tax Concept ID (Identificación del concepto tributario)
*   **Catalog 56:** Public Service Type (Tipo de servicio público)
*   **Catalog 57:** Public Service Type - Telecom (Telecomunicaciones)
*   **Catalog 58:** Meter Type (Tipo de medidor)
*   **Catalog 59:** Payment Methods (Medios de Pago)
*   **Catalog 61:** Related Documents GRE (Documentos relacionados GRE)
*   **And more:** Generic tables and CIIU activities.

## Installation
Install this module as a dependency for other Peruvian localization modules. It requires the base `l10n_pe` module.

## Usage
Data is loaded automatically. You can view the catalogs in the database (typically under Accounting > Configuration > Localization or similar menus if views are exposed).

## Author
**Grupo YACCK**
[www.grupoyacck.com](http://www.grupoyacck.com)
