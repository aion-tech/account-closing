/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { attr } from '@mail/model/model_field';
registerPatch({
    name: 'MessageActionView',
    fields: {
        classNames: {
            compute() {
                //console.dir(this.messageAction.messageActionListOwner)
                if (this.messageAction.messageActionListOwner == this.messageAction.messageActionListOwnerAsCleanedBodyLLM) {
                    classNames = []
                    console.log("helooo2")
                    classNames.push(this.paddingClassNames);
                    classNames.push('fa fa-lg fa-check o_MessageActionView_actionMarkAsRead');
                    console.dir(classNames)
                    return classNames.join(' ')
                }
                return this._super();

            }
        },
    },

});


