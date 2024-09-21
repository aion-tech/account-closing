/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Message } from "@mail/components/message/message";

Message.include({
    toggleMessageBody: function () {
        const messageContentElement = this.el.querySelector('#messageContent');
        if (this.showCleanedBody) {
            messageContentElement.textContent = this.props.message.body;  // Show original body
        } else {
            messageContentElement.textContent = this.props.message.cleanedBody;  // Show cleaned body
        }
        this.showCleanedBody = !this.showCleanedBody;
    }
});
