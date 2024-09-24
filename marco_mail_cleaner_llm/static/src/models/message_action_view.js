/** @odoo-module **/


import { registerPatch } from '@mail/model/model_core';
import { attr } from '@mail/model/model_field';
registerPatch({
    name: 'MessageActionView',
    recordMethods: {
        onClick(ev) {
            if (this.messageAction.messageActionListOwner ==
                  this.messageAction.messageActionListOwnerAsCleanedBodyLLM) {
              console.log("Yuppi");
            }
            return this._super();
        },
    },
    fields: {

        classNames: {
            compute() {
                if (this.messageAction.messageActionListOwner ==
                      this.messageAction.messageActionListOwnerAsCleanedBodyLLM) {
                    console.log("helooo2")
                    const names = [];
                    names.push(this.paddingClassNames);
                    names.push('fa fa-lg fa-eye o_MessageActionView_actionMarkAsRead');
                    console.dir(names)
                    return names.join(' ')
                }
                return this._super();

            }
        },
    },

});
