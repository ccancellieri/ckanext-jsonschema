export const initialize = () => {
        // window.JSONEditor.theme.options = {
    //     "input_size": "small",
    //     "custom_forms": true,
    //     "object_indent": true,
    //     "object_background": "bg-dark",
    //     "table_border": true,
    //     "table_zebrastyle": true
    // }
    
    // window.JSONEditor.defaults.options.colorpicker = {
    //         "editor": false, /* default no editor */
    //         "alpha": false, /* default no alpha */
    //         "editorFormat": "rgb", 
    //         "popup": 'up' /*bottom show in the bottom */
    // }
    window.JSONEditor.defaults.callbacks = {
        "template": {
            "view_template": (jseditor,e) => {

                if (!e || !e.id || e.id == '' || !isValidUUID(e.id)) {
                    return "Please set a view id";
                }
                
                var url = new URL('jsonschema/describe?view_id='+e.id, jsonschema.ckan_url);
                var request = new XMLHttpRequest();
                request.open('GET', url, false);  // `false` makes the request synchronous
                request.send(null);

                if (request.status === 200) {
                    const res = JSON.parse(request.response);
                    return res.resource_name+" - "+res.dataset_title;
                } else {
                    console.error("Unable to resolve item: "+e.id+".\n Response: "+request.response);
                    return "";
                }
                
                // asynch ???
                /*return fetch(url).then(function (response) {
                        return response.json();
                    }).then(function (data) {
                        resolve(data);
                    }).catch(function (err) {
                        console.error(err);
                        return "";
                    });;*/
            }
        },
        "autocomplete": {
        // This is callback functions for the "autocomplete" editor
        // In the schema you refer to the callback function by key
        // Note: 1st parameter in callback is ALWAYS a reference to the current editor.
        // So you need to add a variable to the callback to hold this (like the
        // "jseditor_editor" variable in the examples below.)

        // Setup API calls
            "view_search": function search(jseditor_editor, input) {
                var url = new URL('jsonschema/search?'+
                        'resource_name='+ encodeURI(input)+
                        '&dataset_title='+ encodeURI(input)+
                        '&dataset_description='+ encodeURI(input),jsonschema.ckan_url);
                if (input.length < 2) {
                    return [];
                }
                return fetch(url).then(function (request) {
                        if (request.status === 200) {
                            return request.json();
                        } else {
                            return [""];
                        }
                    }).catch(function (err) {
                        console.error(err);
                        return "";
                    });
            }
        }
    }
}