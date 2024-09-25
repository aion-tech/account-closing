/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { attr } from '@mail/model/model_field';
registerPatch({
    name: 'Message',
    fields: {
        /**
         * Determines whether this message should have the swiper feature, and
         * if so contains the component managing this feature.
         */
        show_cleaned_body: attr({
            default: true,
        }),
        cleaned_body: attr({
            default: "",
        }),
        
        
    },
    modelMethods:{
        convertData(data) {
            const result = this._super(data); // Call the original method
        
            // Add cleaned_body to the converted data if it exists
            if ('cleaned_body' in data) {
                result.cleaned_body = data.cleaned_body;
            }
           /*  if ('show_cleaned_body' in data) {
                result.show_cleaned_body = data.show_cleaned_body;
            } */
        
            return result;
        }, 
       /*  async toggleShowCleanedBody() {
            await this.messaging.rpc({
                model: 'mail.message',
                method: 'toggle_show_cleaned_body',
                args: [[this.id]]
            });
        }, */
    }
});

