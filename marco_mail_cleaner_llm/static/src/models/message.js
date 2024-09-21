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
        cleaned_body: attr({
            default: "",
        }),
        
    },
    modelMethods:{
        convertData(data) {
            const result = this._super(data); // Call the original method
            console.log("cippppaaaa")
            // Add cleaned_body to the converted data if it exists
            if ('cleaned_body' in data) {
                console.log("lippaaaa")
                result.cleaned_body = data.cleaned_body;
            }
        
            return result;
        }, 
    }
});


//import { patch } from "@web/core/utils/patch";
//import Message from '@mail/models/message';
console.log("sono stato letto")

/* 
patch(Message.prototype, 'marco_mail_cleaner_llm.Message', {
   
   cleaned_body: {
       type: String,
       required: true,
   },
   
   
});*/

