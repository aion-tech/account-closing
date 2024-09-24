/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { one } from '@mail/model/model_field';
registerPatch({
    name: 'MessageAction',
    fields: {
        messageActionListOwnerAsCleanedBodyLLM: one('MessageActionList', {
            identifying: true,
            inverse: 'actionCleanedBodyLLM',
        }),

        messageActionListOwner: {
            compute() {
                if (this.messageActionListOwnerAsCleanedBodyLLM)
                    return this.messageActionListOwnerAsCleanedBodyLLM;
                return this._super();
            }
        },

    },

});
