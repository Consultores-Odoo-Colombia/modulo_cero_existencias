/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component, onWillUpdateProps } from "@odoo/owl";

export class StockAvailabilityIcon extends Component {
    static template = "modulo_cero_existencias.StockAvailabilityIcon";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        this.stockInfo = this.getStockInfo(this.props);
        onWillUpdateProps((nextProps) => {
            this.stockInfo = this.getStockInfo(nextProps);
        });
    }

    getStockInfo(props) {
        // Access record data
        const data = props.record.data;

        // Ensure we have the necessary fields
        // Note: The view must include these fields, even if invisible
        const qty = data.quantity || data.qty || data.product_uom_qty || 0;
        const virtualAvailable = data.virtual_available_at_date || 0;
        const productId = data.product_id;

        // Default state
        let color = "text-muted";
        let icon = "fa-bar-chart";
        let title = "No Product";
        let isInvalid = false;

        if (productId) {
            if (virtualAvailable <= 0) {
                color = "text-danger"; // Red for 0 or negative stock
                title = "No Stock Available (" + virtualAvailable + ")";
                isInvalid = true;
            } else if (qty > virtualAvailable) {
                color = "text-warning"; // Orange if requested > available
                title = "Insufficient Stock (Req: " + qty + ", Avail: " + virtualAvailable + ")";
                isInvalid = true;
            } else {
                color = "text-success"; // Green if all good
                title = "Stock Available (" + virtualAvailable + ")";
            }
        }

        return { color, icon, title, isInvalid, virtualAvailable };
    }
}

export const stockAvailabilityIcon = {
    component: StockAvailabilityIcon,
};

registry.category("view_widgets").add("stock_availability_icon", stockAvailabilityIcon);
