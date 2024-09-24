/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { one} from '@mail/model/model_field';
registerPatch({
    name: 'MessageActionList',
    fields: {
       
        actionCleanedBodyLLM: one('MessageAction', {
            compute() {
                console.log("actionCleanedBodyLLM")
                return {};
            },
            inverse: 'messageActionListOwnerAsCleanedBodyLLM',
        }),
        
    },
    
});
