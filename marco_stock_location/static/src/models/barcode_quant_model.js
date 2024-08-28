/** @odoo-module **/

import BarcodeModel from "@stock_barcode/models/barcode_model";
import MainComponent from "@stock_barcode/components/main";
import { patch } from "web.utils";

import BarcodeParser from "barcodes.BarcodeParser";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Mutex } from "@web/core/utils/concurrency";
import LazyBarcodeCache from "@stock_barcode/lazy_barcode_cache";
import { _t } from "web.core";
import { sprintf } from "@web/core/utils/strings";
import { useService } from "@web/core/utils/hooks";

const { EventBus } = owl;

function parseNumber(numberString) {
  // Rimuovi eventuali spazi
  numberString = numberString.trim();

  // Verifica se il numero contiene sia un punto che una virgola
  if (numberString.includes(',') && numberString.includes('.')) {
      // Controlla se l'ultima virgola viene dopo l'ultimo punto
      if (numberString.lastIndexOf(',') > numberString.lastIndexOf('.')) {
          // Tratta come formato europeo (1.234,56)
          numberString = numberString.replace('.', '').replace(',', '.');
      } else {
          // Tratta come formato americano (1,234.56)
          numberString = numberString.replace(',', '');
      }
  } else if (numberString.includes(',')) {
      // Tratta come formato europeo se contiene solo una virgola (1.234,56)
      numberString = numberString.replace('.', '').replace(',', '.');
  }

  // Converti la stringa in un numero float
  return parseFloat(numberString);
}

patch(MainComponent.prototype, "marco_stock_location_main_component", {
  /**
   * Handler called when a barcode is scanned.
   *
   * @private
   * @param {string} barcode
   */
  _onBarcodeScanned(barcode) {
    if (this.displayBarcodeApplication) {
      this.env.model.processBarcode(barcode);
    }
  },
});

patch(BarcodeModel.prototype, "marco_stock_location_barcode_model", {
  async processBarcode(barcode) {
    this.actionMutex.exec(() => this._processBarcode(barcode));
  },

  async _processBarcode(barcode) {
    let barcodeData = {};
    let currentLine = false;
    // Creates a filter if needed, which can help to get the right record
    // when multiple records have the same model and barcode.
    const filters = {};
    if (this.selectedLine && this.selectedLine.product_id.tracking !== "none") {
      filters["stock.lot"] = {
        product_id: this.selectedLine.product_id.id,
      };
    }
    try {
      barcodeData = await this._parseBarcode(barcode, filters);
      if (
        !barcodeData.match &&
        filters["stock.lot"] &&
        !this.canCreateNewLot &&
        this.useExistingLots
      ) {
        // Retry to parse the barcode without filters in case it matches an existing
        // record that can't be found because of the filters
        const lot = await this.cache.getRecordByBarcode(barcode, "stock.lot");
        if (lot) {
          Object.assign(barcodeData, { lot, match: true });
        }
      }
    } catch (parseErrorMessage) {
      barcodeData.error = parseErrorMessage;
    }

    // Keep every scan in memory.
    this.scanHistory.unshift(barcodeData);

    // Process each data in order, starting with non-ambiguous data type.
    if (barcodeData.action) {
      // As action is always a single data, call it and do nothing else.
      return await barcodeData.action();
    }
    // Depending of the configuration, the user can be forced to scan a specific barcode type.
    const check = this._checkBarcode(barcodeData);
    if (check.error) {
      return this.notification.add(check.message, {
        title: check.title,
        type: "danger",
      });
    }

    if (barcodeData.packaging) {
      Object.assign(barcodeData, this._retrievePackagingData(barcodeData));
    }

    if (barcodeData.product) {
      // Remembers the product if a (packaging) product was scanned.
      this.lastScanned.product = barcodeData.product;
    }

    if (barcodeData.lot && !barcodeData.product) {
      Object.assign(
        barcodeData,
        this._retrieveTrackingNumberInfo(barcodeData.lot),
      );
    }

    await this._processLocation(barcodeData);
    await this._processPackage(barcodeData);
    if (barcodeData.stopped) {
      // TODO: Sometime we want to stop here instead of keeping doing thing,
      // but it's a little hacky, it could be better to don't have to do that.
      return;
    }

    if (barcodeData.weight) {
      // Convert the weight into quantity.
      barcodeData.quantity = barcodeData.weight.value;
    }

    // If no product found, take the one from last scanned line if possible.
    if (!barcodeData.product) {
      if (barcodeData.quantity) {
        currentLine = this.selectedLine || this.lastScannedLine;
      } else if (
        this.selectedLine &&
        this.selectedLine.product_id.tracking !== "none"
      ) {
        currentLine = this.selectedLine;
      } else if (
        this.lastScannedLine &&
        this.lastScannedLine.product_id.tracking !== "none"
      ) {
        currentLine = this.lastScannedLine;
      }
      if (currentLine) {
        // If we can, get the product from the previous line.
        const previousProduct = currentLine.product_id;
        // If the current product is tracked and the barcode doesn't fit
        // anything else, we assume it's a new lot/serial number.
        if (
          previousProduct.tracking !== "none" &&
          !barcodeData.match &&
          this.canCreateNewLot
        ) {
          barcodeData.lotName = barcode;
          barcodeData.product = previousProduct;
        }
        if (barcodeData.lot || barcodeData.lotName || barcodeData.quantity) {
          barcodeData.product = previousProduct;
        }
      }
    }
    let { product } = barcodeData;
    if (
      !product &&
      barcodeData.match &&
      this.parser.nomenclature.is_gs1_nomenclature
    ) {
      // Special case where something was found using the GS1 nomenclature but no product is
      // used (eg.: a product's barcode can be read as a lot is starting with 21).
      // In such case, tries to find a record with the barcode by by-passing the parser.
      barcodeData = await this._fetchRecordFromTheCache(barcode, filters);
      if (barcodeData.packaging) {
        Object.assign(barcodeData, this._retrievePackagingData(barcodeData));
      } else if (barcodeData.lot) {
        Object.assign(
          barcodeData,
          this._retrieveTrackingNumberInfo(barcodeData.lot),
        );
      }
      if (barcodeData.product) {
        product = barcodeData.product;
      } else if (barcodeData.match) {
        await this._processPackage(barcodeData);
        if (barcodeData.stopped) {
          return;
        }
      }
    }
    if (!product) {
      // Product is mandatory, if no product, raises a warning.
      if (!barcodeData.error) {

        if (this.selectedLine && !barcode.startsWith("92M") && /^[^a-zA-Z]*$/.test(barcode)) {
          // Verifica che il barcode sia numerico
          if(barcode.length >= 8 && !numberString.includes(',') && !numberString.includes('.')){
            return this.notification.add(_t(
              "Codice non esiste o qty troppo grande",
              ), { type: "error" });
          }
          const quantity = parseNumber(barcode);

          let line = this.pageLines.find(
            (l) => l.virtual_id === this.selectedLine.virtual_id,
          );

          if (line) {
            line.inventory_quantity = quantity;
            this.trigger("update");
            console.log(line)
            let msg=String(quantity)+" "+ this.cache.getRecord("uom.uom", line.product_id.uom_id).name+" set for "+ line.product_id.default_code 
            return this.notification.add(_t(
            String(msg),
            ), { type: "success" });
           
          }
        }

        if (this.groups.group_tracking_lot) {
          barcodeData.error = _t(
            "You are expected to scan one or more products or a package available at the picking location",
          );
        } else {
          barcodeData.error = _t(
            "You are expected to scan one or more products.",
          );
        }
      }
      return this.notification.add(barcodeData.error, { type: "danger" });
    } else if (barcodeData.lot && barcodeData.lot.product_id !== product.id) {
      delete barcodeData.lot; // The product was scanned alongside another product's lot.
    }
    if (barcodeData.weight) {
      // the encoded weight is based on the product's UoM
      barcodeData.uom = this.cache.getRecord("uom.uom", product.uom_id);
    }

    // Searches and selects a line if needed.
    if (
      !currentLine ||
      this._shouldSearchForAnotherLine(currentLine, barcodeData)
    ) {
      currentLine = this._findLine(barcodeData);
    }

    // Default quantity set to 1 by default if the product is untracked or
    // if there is a scanned tracking number.
    if (
      product.tracking === "none" ||
      barcodeData.lot ||
      barcodeData.lotName ||
      this._incrementTrackedLine()
    ) {
      const hasUnassignedQty =
        currentLine &&
        currentLine.qty_done &&
        !currentLine.lot_id &&
        !currentLine.lot_name;
      const isTrackingNumber = barcodeData.lot || barcodeData.lotName;
      const defaultQuantity = isTrackingNumber && hasUnassignedQty ? 0 : 1;
      barcodeData.quantity = barcodeData.quantity || defaultQuantity;
      if (
        product.tracking === "serial" &&
        barcodeData.quantity > 1 &&
        (barcodeData.lot || barcodeData.lotName)
      ) {
        barcodeData.quantity = 1;
        this.notification.add(
          _t(
            `A product tracked by serial numbers can't have multiple quantities for the same serial number.`,
          ),
          { type: "danger" },
        );
      }
    }

    if ((barcodeData.lotName || barcodeData.lot) && product) {
      const lotName = barcodeData.lotName || barcodeData.lot.name;
      for (const line of this.currentState.lines) {
        if (
          line.product_id.tracking === "serial" &&
          this.getQtyDone(line) !== 0 &&
          ((line.lot_id && line.lot_id.name) || line.lot_name) === lotName
        ) {
          return this.notification.add(
            _t("The scanned serial number is already used."),
            { type: "danger" },
          );
        }
      }
      // Prefills `owner_id` and `package_id` if possible.
      const prefilledOwner =
        (!currentLine || (currentLine && !currentLine.owner_id)) &&
        this.groups.group_tracking_owner &&
        !barcodeData.owner;
      const prefilledPackage =
        (!currentLine || (currentLine && !currentLine.package_id)) &&
        this.groups.group_tracking_lot &&
        !barcodeData.package;
      if (this.useExistingLots && (prefilledOwner || prefilledPackage)) {
        const lotId =
          (barcodeData.lot && barcodeData.lot.id) ||
          (currentLine && currentLine.lot_id && currentLine.lot_id.id) ||
          false;
        const res = await this.orm.call(
          "product.product",
          "prefilled_owner_package_stock_barcode",
          [product.id],
          {
            lot_id: lotId,
            lot_name: (!lotId && barcodeData.lotName) || false,
            context: { location_id: currentLine.location_id },
          },
        );
        this.cache.setCache(res.records);
        if (prefilledPackage && res.quant && res.quant.package_id) {
          barcodeData.package = this.cache.getRecord(
            "stock.quant.package",
            res.quant.package_id,
          );
        }
        if (prefilledOwner && res.quant && res.quant.owner_id) {
          barcodeData.owner = this.cache.getRecord(
            "res.partner",
            res.quant.owner_id,
          );
        }
      }
    }

    // Updates or creates a line based on barcode data.
    if (currentLine) {
      // If line found, can it be incremented ?
      let exceedingQuantity = 0;
      if (
        product.tracking !== "serial" &&
        barcodeData.uom &&
        barcodeData.uom.category_id == currentLine.product_uom_id.category_id
      ) {
        // convert to current line's uom
        barcodeData.quantity =
          (barcodeData.quantity / barcodeData.uom.factor) *
          currentLine.product_uom_id.factor;
        barcodeData.uom = currentLine.product_uom_id;
      }
      // Checks the quantity doesn't exceed the line's remaining quantity.
      if (currentLine.reserved_uom_qty && product.tracking === "none") {
        const remainingQty =
          currentLine.reserved_uom_qty - currentLine.qty_done;
        if (barcodeData.quantity > remainingQty) {
          // In this case, lowers the increment quantity and keeps
          // the excess quantity to create a new line.
          exceedingQuantity = barcodeData.quantity - remainingQty;
          barcodeData.quantity = remainingQty;
        }
      }
      if (barcodeData.quantity > 0 || barcodeData.lot || barcodeData.lotName) {
        const fieldsParams = this._convertDataToFieldsParams(barcodeData);
        if (barcodeData.uom) {
          fieldsParams.uom = barcodeData.uom;
        }
        await this.updateLine(currentLine, fieldsParams);
      }
      if (exceedingQuantity) {
        // Creates a new line for the excess quantity.
        barcodeData.quantity = exceedingQuantity;
        const fieldsParams = this._convertDataToFieldsParams(barcodeData);
        if (barcodeData.uom) {
          fieldsParams.uom = barcodeData.uom;
        }
        currentLine = await this._createNewLine({
          copyOf: currentLine,
          fieldsParams,
        });
      }
    } else {
      // No line found, so creates a new one.
      const fieldsParams = this._convertDataToFieldsParams(barcodeData);
      if (barcodeData.uom) {
        fieldsParams.uom = barcodeData.uom;
      }
      currentLine = await this.createNewLine({ fieldsParams });
    }

    // And finally, if the scanned barcode modified a line, selects this line.
    if (currentLine) {
      this._selectLine(currentLine);
    }
    this.trigger("update");
  },
});
