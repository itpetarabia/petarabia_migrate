odoo.define('pos_debt_notebook.ClientDetailsEdit', function(require) {
    'use strict';

    const { getDataURLFromFile } = require('web.utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');

    const PosNotebookClientDetailsEdit = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);

            }

        };

    Registries.Component.extend(ClientDetailsEdit, PosNotebookClientDetailsEdit);

    return ClientDetailsEdit;
});


        /*
        mounted() {
            this.env.bus.on('save-customer', this, this.saveChanges);
        }
        willUnmount() {
            this.env.bus.off('save-customer', this);
        }
        get partnerImageUrl() {
            // We prioritize image_1920 in the `changes` field because we want
            // to show the uploaded image without fetching new data from the server.
            const partner = this.props.partner;
            if (this.changes.image_1920) {
                return this.changes.image_1920;
            } else if (partner.id) {
                return `/web/image?model=res.partner&id=${partner.id}&field=image_128&write_date=${partner.write_date}&unique=1`;
            } else {
                return false;
            }
        }
        captureChange(event) {
            this.changes[event.target.name] = event.target.value;
        }
        saveChanges() {
            let processedChanges = {};
            for (let [key, value] of Object.entries(this.changes)) {
                if (this.intFields.includes(key)) {
                    processedChanges[key] = parseInt(value) || false;
                } else {
                    processedChanges[key] = value;
                }
            }
            if ((!this.props.partner.name && !processedChanges.name) ||
                processedChanges.name === '' ){
                return this.showPopup('ErrorPopup', {
                  title: _('A Customer Name Is Required'),
                });
            }
            processedChanges.id = this.props.partner.id || false;
            this.trigger('save-changes', { processedChanges });
        }
        */

