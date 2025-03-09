odoo.define("appointments_web_calendar_color.CalendarModel", function (require) {
    "use strict";

    const CalendarModel = require("web.CalendarModel");

    CalendarModel.include({

        _loadColors: function (element, events) {
            //console.log("_loadColors0000",element, events,this)
            if (this.fieldColor) {
                var fieldName = this.fieldColor;
                var filter = this.data.filters[fieldName];
                //console.log("filter0000",filter);
                if (this.modelName === "pos.appointments") {
                    _.each(events, function (event) {
                        var value = event.record[fieldName];
                        if (event.record.state && ['order','ready','done','paid'].includes(event.record.state)){
                            if (event.record.state === 'order'){
                                event.color_index = 19;
                            }
                            if (event.record.state === 'ready'){
                                event.color_index = 8;
                                //console.log("typeof color",typeof event.color_index);
                            }
                            if (event.record.state === 'done'){
                                event.color_index = 28;
                            }
                            if (event.record.state === 'paid'){
                                event.color_index = 28;
                            }
                        } else{
                            event.color_index = _.isArray(value) ? value[0] : value;
                            //event.color_index = 3;
                        }

                    });
                    this.model_color = this.fields[fieldName].relation || element.model;

                } else {
                    return this._super.apply(this, arguments);
                }

            }
            return Promise.resolve();
        },
    });

    return CalendarModel;
});
