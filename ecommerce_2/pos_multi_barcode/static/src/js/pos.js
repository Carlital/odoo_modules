import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { DataServiceOptions } from "@point_of_sale/app/models/data_service_options";





patch(PosStore.prototype, {
    async processServerData(loadedData) {
        await super.processServerData(...arguments);
        this.em_uom_list = this.models['pos.multi.barcode'].getAll();
    },
});

patch(DataServiceOptions.prototype, {


    get databaseIndex() {
        var indexes = super.databaseIndex;
        indexes['pos.multi.barcode'] = ["name"]
        return indexes;
    }
});


patch(ProductScreen.prototype, {
    async _getProductByBarcode(code) {
        var product = await super._getProductByBarcode(...arguments);
        if (! product) {
            const productMultibar = this.pos.models["pos.multi.barcode"].getBy(
                "name",
                code.base_code
            );
            if(productMultibar){
                product = productMultibar.product_id;
            }
        }
        return product;

    },



});

