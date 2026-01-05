/** @odoo-module **/

import { SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";

export class StockRestrictedListRenderer extends SectionAndNoteListRenderer {
    static rowsTemplate = "modulo_cero_existencias.StockRestrictedListRenderer.Rows";

    get displayRowCreates() {
        const shouldBlock = this.shouldBlockCreation();
        console.log("[StockRestricted] displayRowCreates check:", shouldBlock);
        
        // Check if we should block creation
        if (shouldBlock) {
            return false;
        }
        return super.displayRowCreates;
    }

    shouldBlockCreation() {
        // Iterate over records to check for stock issues
        // We look for the status set by our widget logic or checking fields directly
        for (const record of this.props.list.records) {
            const data = record.data;
            const virtualAvailable = data.virtual_available_at_date || 0;
            const qty = data.quantity || data.qty || data.product_uom_qty || 0;
            const productId = data.product_id;

            // Debug logic
            // console.log("Checking record:", record.resId, "Prod:", productId, "Qty:", qty, "Avail:", virtualAvailable);

            // Strict check: If product is selected AND (avail <= 0 OR qty > avail)
            if (productId && (virtualAvailable <= 0 || qty > virtualAvailable)) {
                console.log("[StockRestricted] BLOCKING due to record:", record.resId);
                return true; 
            }
        }
        return false;
    }
}

export const stockRestrictedListView = {
    ...listView,
    Renderer: StockRestrictedListRenderer,
};

registry.category("views").add("stock_restricted_list", stockRestrictedListView);
