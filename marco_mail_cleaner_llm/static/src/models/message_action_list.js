/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { one } from '@mail/model/model_field';
import { clear } from '@mail/model/model_field_command';

registerPatch({
    name: 'MessageActionList',
    fields: {
        
        actionCleanedBodyLLM: one('MessageAction', {
            compute() {
                if (this.message && this.message.cleaned_body)
                    return {};
                return clear();
            },
            inverse: 'messageActionListOwnerAsCleanedBodyLLM',
        }),
        
    },
    
});
