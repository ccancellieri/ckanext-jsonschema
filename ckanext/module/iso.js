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
            }
        },
        "autocomplete": {
        // This is callback functions for the "autocomplete" editor
        // In the schema you refer to the callback function by key
        // Note: 1st parameter in callback is ALWAYS a reference to the current editor.
        // So you need to add a variable to the callback to hold this (like the
        // "jseditor_editor" variable in the examples below.)
            // SECTION TAG
            "tag_keywords_autocomplete": (jseditor_editor, input) => {
                if (input.length < 2) {
                    return [];
                }
                let _url = 'api/3/action/tag_autocomplete?query='+encodeURI(input)

                let url = new URL(_url, jsonschema.ckan_url);

                return window.JSONEditor.defaults.callbacks.autocomplete.jsonschema_fetch(jseditor_editor, url);
            },
            "tag_specialized_keywords_autocomplete": (jseditor_editor, input) => {
                if (input.length < 2) {
                    return [];
                }
                let _url = 'api/3/action/tag_autocomplete?query='+encodeURI(input)
                
                let vocab_name = jseditor_editor.parent.parent.getValue().type
                if (vocab_name){
                    // TODO document python code vocab name convention
                    vocab_name='iso__keywords__'+vocab_name
                    // TODO escape with keywords
                    _url = _url +'&vocabulary_id=' + encodeURI(vocab_name)
                }

                let url = new URL(_url, jsonschema.ckan_url);

                return window.JSONEditor.defaults.callbacks.autocomplete.jsonschema_fetch(jseditor_editor, url);
            },
            "tag_render": (jseditor_editor, result, props) => {
                return ['<li ' + props + '>',
                    '<div>' + result + '</div>',
                    '</li>'].join('');
            },
            "tag_getResultValue": (jseditor_editor, result)=>result,
            //SECTION REFERENCE SYSTEM IDENTIFIER (PROJECTION)
            "reference_system_identifier_autocomplete": (jseditor_editor, input) => {
                if (input.length < 3) {
                    return [];
                }
                let _url = 'https://epsg.io/?q=' + encodeURI(input) + '&format=json'

                let url = new URL(_url);

                return fetch(url)
                        .then((request)=> {
                            if (request.status === 200) {
                                return request.json();
                            } else {
                                return [];
                            }
                        }).catch((err)=> {
                            console.error(err);
                            return [];
                        }).then(result=> {
                            if (result.status === "ok"){
                                return result.results.map(el => el.name);
                            }
                            return [];
                        });
            },
            "reference_system_identifier_getResultValue": (jseditor_editor, result) => result,
            "reference_system_identifier_render" : (jseditor_editor, result, props) => {
                return ['<li ' + props + '>',
                    '<div>' + result + '</div>',
                    '</li>'].join('');
            },
            // TODO keywords match into json schema
            "jsonschema_fetch": (jseditor_editor, url) => {
                
                return fetch(url)
                        .then((request)=>{
                            if (request.status === 200) {
                                return request.json();
                            } else {
                                return [];
                            }
                        }).catch((err)=>{
                            console.error(err);
                            return [];
                        }).then(result=>{
                            if (result.success===true){
                                return result.result;
                            }
                            return [];
                        });
            },
        }
    }
}