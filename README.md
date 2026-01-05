# Restricción de Ventas en Cero

## Resumen
Impide confirmar facturas (Cliente/Proveedor), notas de crédito y pedidos POS con monto cero.

## Descripción
Este módulo añade una validación estricta para evitar que se procesen facturas de cliente y proveedor (`account.move`), así como notas de crédito y pedidos de punto de venta (`pos.order`) con un monto total de 0.

## Características
*   **Validación de Facturas y Notas:** Impide la confirmación de facturas (Cliente/Proveedor) y rectificativas si el monto total es 0.
*   **Validación de Stock (Ventas):** Impide confirmar Órdenes de Venta si no hay suficiente stock a mano (qty_available).
*   **Validación de POS:** Impide la creación de pedidos de punto de venta si el monto total es 0.

## Instalación
Instalar como un módulo estándar de Odoo.

## Créditos
*   **Autor:** consultoresodoocolombia
*   **Sitio Web:** [https://consultoresodoocolombia.odoo.com/](https://consultoresodoocolombia.odoo.com/)
