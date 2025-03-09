odoo.define('partner_disclaimer_sign_pos.ClientDetailsEdit', function(require) {

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const { getDataURLFromFile } = require('web.utils');
    var download = require('web.download');
    //const session = require('web.session');

    const DisclaimerSignClientDetailsEdit = ClientDetailsEdit => class extends ClientDetailsEdit {
         constructor() {
             super(...arguments);
             //console.log('ClientDetailsEdit constructor ext')
         }
         getMimeType(b64) {
             var signatures = {
              JVBERi0: "application/pdf",
              R0lGODdh: "image/gif",
              R0lGODlh: "image/gif",
              iVBORw0KGgo: "image/png",
             '/9j/4AAQSkZJ':"image/jpg",
             '/9j/4AAQSkZJRgA':"image/jpeg",

            };
          for (var s in signatures) {
            if (b64.indexOf(s) === 0) {
              return signatures[s];
            }
          }
          return undefined;
        }
         mounted() {
            //console.log('mounted ext');
            super.mounted();
            if (this.props.partner.id == undefined) {
                this.show_hide_div_disclaimer_sign_doc(false);
                this.show_hide_disclaimer_sign_doc(false);
                this.show_hide_download_sign(false);
                this.show_hide_delete_sign(false);
            }
            else {
                this.show_hide_div_disclaimer_sign_doc(this.props.partner.disclaimer_sign && !this.props.partner.disclaimer_sign_doc);
                //checkbox
                if (this.props.partner.disclaimer_sign)
                    $(".client-disclaimer_sign").prop('checked', true);
                //choose file
                this.show_hide_disclaimer_sign_doc(this.props.partner.disclaimer_sign && !this.props.partner.disclaimer_sign_doc);
                //download icon
                this.show_hide_download_sign(this.props.partner.disclaimer_sign_doc && this.props.partner.disclaimer_sign);
                //delete icon
                this.show_hide_delete_sign(this.props.partner.disclaimer_sign_doc && this.props.partner.disclaimer_sign);
            }
         }
         show_hide_download_sign(has)
         {
             //console.log('show_hide_download_sign=',has);
             if(has == false)
                 $(".download-sign").css("display", "none");
             else
                 $(".download-sign").css("display", "");
         }
         show_hide_delete_sign(has)
         {
             //console.log('show_hide_delete_sign=',has);
             if(has == false)
                 $(".delete-sign").css("display", "none");
             else
                 $(".delete-sign").css("display", "");
         }
         show_hide_disclaimer_sign_doc(has_doc)
         {
            if (has_doc == false) {
                 $(".client-disclaimer_sign_doc").css("display", "none");
             }
            else {
                 $(".client-disclaimer_sign_doc").css("display", '');
             }
         }
         show_hide_div_disclaimer_sign_doc(has_sign)
         {
             if (has_sign == false) {
                 $(".div_disclaimer_sign_doc").css("display", "none");
             }
            else {
                 $(".div_disclaimer_sign_doc").css("display", "");
             }
         }
         async deleteSign(event) {
            this.changes['disclaimer_sign_doc'] = '';
            this.show_hide_download_sign(false);
            this.show_hide_div_disclaimer_sign_doc(true);
            this.show_hide_disclaimer_sign_doc(true);
            this.show_hide_delete_sign(false);
         }
         async downloadSign(event) {
             ////console.log('downloadSign=',this);
             const partner_edit = this.props.partner;
             let disclaimer_sign_doc = this.changes.disclaimer_sign_doc || partner_edit.disclaimer_sign_doc;
             if(disclaimer_sign_doc) {
                 let base_64 = '';
                 let mim_type = this.getMimeType(disclaimer_sign_doc);
                 let file_name = this.changes.name || partner_edit.name+"-"+"dclmr sign";
                 if (mim_type) {
                     base_64 = "data:"+mim_type+";base64,";
                     file_name += "."+mim_type.split("/")[1];
                 }
                 ////console.log('mim_type=',mim_type,file_name);
                 await download(base_64+disclaimer_sign_doc, file_name, mim_type);
             }
         }
        captureChange_disclaimer_sign(event) {
            //download('Testttttttt', 'exported_employees.txt', 'text/plain');
            //console.log('captureChange_disclaimer_sign = ', event.target.checked)
            this.changes[event.target.name] = event.target.checked;
            this.show_hide_div_disclaimer_sign_doc(event.target.checked);
            this.changes['disclaimer_sign_doc'] = '';
            this.show_hide_download_sign(false);
            this.show_hide_delete_sign(false);
            if (event.target.checked == true)
                this.show_hide_disclaimer_sign_doc(true);

        }
        async uploadSignFile(event) {
            const file = event.target.files[0];
            //console.log('uploadSignFile=',event.target.files);
            if (file == undefined) {
                this.changes[event.target.name] = '';
                this.show_hide_disclaimer_sign_doc(false);
            }
            else
            {
                //console.log('file=',file)
                const signUrl = await getDataURLFromFile(file);
                //this.changes - from - captureChange
                this.changes[event.target.name] = signUrl.split(',')[1];
                this.show_hide_disclaimer_sign_doc(true);
                //console.log('signUrl=',signUrl)
            }




            //if (!file.type.match(/image.*/))
            /*
            {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Unsupported File Format'),
                    body: this.env._t(
                        'Only web-compatible Image formats such as .png or .jpeg are supported.'
                    ),
                });
            } else {
                const imageUrl = await getDataURLFromFile(file);
                const loadedImage = await this._loadImage(imageUrl);
                if (loadedImage) {
                    const resizedImage = await this._resizeImage(loadedImage, 800, 600);
                    this.changes.image_1920 = resizedImage.toDataURL();
                    // Rerender to reflect the changes in the screen
                    this.render();
                }
            }
            */
        }
    };

    Registries.Component.extend(ClientDetailsEdit, DisclaimerSignClientDetailsEdit);

    return ClientDetailsEdit;
});
