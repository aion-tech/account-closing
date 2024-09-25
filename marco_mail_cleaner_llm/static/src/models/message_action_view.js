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
             
                this.messageAction.messageActionListOwner.message.update({ show_cleaned_body: !this.messageAction.messageActionListOwner.message.show_cleaned_body });
                   
            }
            
            return this._super();
        },
    },
    fields: {

        classNames: {
            compute() {
                if (this.messageAction.messageActionListOwner ==
                      this.messageAction.messageActionListOwnerAsCleanedBodyLLM) {
                    
                    const names = [];
                    names.push(this.paddingClassNames);
                    
                    names.push('fa fa-lg');
                        if (this.messageAction.messageActionListOwner.message.show_cleaned_body) {
                            names.push('fa-eye');
                        } else {
                            names.push('fa-eye-slash');
                        }
                    
                    return names.join(' ')
                }
                return this._super();

            }
        },
    },

});
