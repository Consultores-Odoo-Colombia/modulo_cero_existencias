/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    async addProductToOrder(product) {
        // Check restriction
        const company = this.pos.company;
        const restrictZeroPos = company && company.restrict_zero_pos;
        
        if (restrictZeroPos && product.type === 'product') {
             const qtyAvailable = product.qty_available;
             
             if (qtyAvailable <= 0) {
                 this.notification.add(_t("No puedes agregar este producto porque el stock a la mano es 0 o negativo."), {
                    type: "danger",
                });
                return;
             }
        }
        
        return super.addProductToOrder(product);
    }
});
