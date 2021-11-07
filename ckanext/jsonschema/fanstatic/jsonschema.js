// json preview module
ckan.module('jsonschema', function (jQuery, _) {
    /* Check if string is valid UUID */
    isValidUUID = (str) => {
        // Regular expression to check if string is a valid UUID
        const regexExp = /^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/gi;
        return regexExp.test(str);
    };

    loadSchema = function (uri) {
        return new Promise((resolve, reject) => {
            function get(retry, uri){
                //resolve(require('./id.json')); // replace with http request for example
                $.ajaxSetup({ timeout: 30000, cache: true });
                $.get({
                    cache: true,
                    url: uri, 
                    success: function(data) {
                        //alert( "success: ");
                        if (data !== null && typeof data !== "object") {
                            data = JSON.parse(data)
                        }
                        resolve(data);
                        return data;
                        // _data=JSON.parse(data)
                        // resolve(_data);
                        // return _data;
                    },
                    fail:function() {
                        //alert( "error" );
                        if (retry>0){
                            get(--retry, uri);
                        } else {
                            reject(new Error(`could not locate ${uri}`));
                        }
                    }
                });
            };
            let retry=3;
            if (uri.startsWith('http')) {
                return get(retry,uri);
            } else {
                //reject(new Error(`could not locate ${uri}`));
                return get(retry,new URL('jsonschema/schema/'+uri, jsonschema.ckan_url));
            }
        });
    };
    
    jsonschema = {
        
        asObject: function (value) {
            try {
                if (value){
                    if (typeof value == "string"){
                        return JSON.parse(value);
                    } else {
                        return value;
                    }
                }
            } catch (err) {
                console.log(err.stack);
            }
            return {};
        },
        asString: function (value) {
            if (value){
                if (typeof value == "string"){
                    return value;
                } else {
                    return JSON.stringify(value, null, '  ');
                }
            }
            return "";
        },
        onSubmit: function (event) {
                if (!this.editor) return;

                // prepare info to serialize
                let value=this.editor.getValue();
                this.jsonschema_body=jsonschema.asObject(value);
//TODO externalize id
                let input=$('#field-_body_')[0]; 
                input.value=jsonschema.asString(value);

                this.editorToggle(enable=false);
        },
        ckan_url: undefined,
        jsonschema_schema: undefined,
        jsonschema_body: undefined,
        editor: undefined,
        initialize: function () {
            var self = this;

            jsonschema.ckan_url = self.options.ckanUrl;
            jsonschema.jsonschema_schema = self.options.schema;
            jsonschema.jsonschema_body = self.options.body;
            jsonschema.jsonschema_opt = self.options.opt;
            jsonschema.jsonschema_type = self.options.type;

            jsonschema.getEditor=this.getEditor.bind(jsonschema);
            jsonschema.getEditorAce=this.getEditorAce.bind(jsonschema);
            jsonschema.editorReady=this.editorReady.bind(jsonschema);
            jsonschema.editorValidate=this.editorReady.bind(jsonschema);
            jsonschema.editorToggle=this.editorToggle.bind(jsonschema);

            jsonschema.wrap=this.wrap.bind(jsonschema);

//jsonschema.onSubmit
            $('.dataset-form').find('button[type=submit]').each(
                function (){$(this).on('click', jsonschema.onSubmit.bind(jsonschema));});

            // jsonschema.getEditorAce();
            jsonschema.getEditor();
        },
        getEditorAce: function (){

            let value;
            if (this.editor && this.editor instanceof window.JSONEditor){
                // save changes in local context
                value=jsonschema.asString(this.editor.getValue());
                this.editor.destroy();
            } else {
                // save changes in local context
                value=jsonschema.asString(jsonschema.jsonschema_body);
            }
            this.isHowto=false

            let schema={
              "type": "string",
              "format": "json",
              "title": "Terria configuration",
              "options": {
                    "ace": {
                      //"theme": "ace/theme/tailwind",
                      "tabSize": 2,
                      "useSoftTabs": true,
                      "wrap": true,
                      //"fontFamily": "tahoma",
                      "fontSize": "14pt"
                      //,"enableBasicAutocompletion": true
                    }
               }
              }
        // Initialize the editor
            this.editor = new JSONEditor(document.getElementById('editor-jsonschema-config'),{
                // Enable fetching schemas via ajax
                ajax: true,
                ajaxBase: new URL('jsonschema/schema/', jsonschema.ckan_url),
//                ajaxCredentials: true

                // The schema for the editor
                schema: schema,

                // Seed the form with a starting value
                startval: value,

                // urn_resolver: (urn, callback) => {
                //         loadSchema(urn)
                //             .then(schema=>{callback(schema);})
                //         return true;
                // },

                // https://github.com/json-editor/json-editor#css-integration
                // barebones, html (the default), bootstrap4, spectre, tailwind
                theme: 'bootstrap3',
                iconlib: "fontawesome4"
                });
            /*JSONEditor.plugins.ace = {
                theme:"tailwind",
              fontFamily: "tahoma",
              fontSize: "12pt"
            };*/
            // import Ajv from "ajv"
            // const ajv = new Ajv.default()
            // const Ajv = require("ajv").default
            
            jsonschema.ajv = new window.ajv7({
                // coerceTypes: true,
                validateFormats: false,
                // validateFormats: false,
                // formats: {'*': true, checkbox: true},
                loadSchema:loadSchema,
                // strict: false,
                // // allErrors: true,
                // validateSchema: false, 
                strictSchema: false
            });

            if (!jsonschema.validate){
                jsonschema.ajv.compileAsync(jsonschema.jsonschema_schema).then(
                    function(val){
                        jsonschema.validate=val;
                        jsonschema.editorOnChange(jsonschema.ajvValidation());
                    }
                ).catch(err => {
                    if (confirm("An error occurred validating the schema: schema not supported by this editor.\n"+
                                "Continuing validation will be disabled, this may allow creating corrupted configurations:\nContinue?")){
                        console.error(err);
                    } else {
                        jsonschema.getEditor();
                        return;
                    }
                });
            }
            this.editor.on('ready',this.editorReady);
            this.editor.on('change',()=>{

                this.editorOnChange(jsonschema.ajvValidation());
            });
            this.editorToggle(true);
        },
        ajvValidation: function () {

            // Get an array of errors from the validator
            if (!jsonschema.editor || !jsonschema.editor.ready){
                return;
            }

            var errors = undefined;
            try {
                let val=JSON.parse(jsonschema.editor.getValue());
                if (jsonschema.validate){
                    if (!jsonschema.validate(val))
                        errors='<div style="height:150px; overflow:auto;" id="outher-error">'+
                            '<table id="inner-error" style="width:100%;">'+
                            '<tr>'+
                                '<th><h2>Message</h2></th>'+
                                '<th><h2>Path</h2></th>'+
                                '<th><h2>Error</h2></th></tr>'+
                                jsonschema.validate.errors.map(
                                    e=>'<tr><td>'+
                                        e.message+'</td><td>'
                                        +e.instancePath+'</td><td>'
                                        +Object.keys(e.params).map(m=>m+' : '+e.params[m]).reduce((a,c)=>a+c,'')+'</td></tr>'
                                ).reduce((a,c,i)=>a+c,'')+
                            '</table></div>';
                }
                return {'html':errors, 'lock':true};
            } catch (exc) {
                errors='<p>'+exc+'</p>';
                return {'html':errors, 'lock':true};
            }

        },
        getEditor: function (_schema){
            let schema;
            if (_schema){
                schema = _schema;
            }
            schema = jsonschema.jsonschema_schema;

            let value;
            if (this.editor && this.editor instanceof window.JSONEditor){
                // save changes in local context
                value=jsonschema.asObject(this.editor.getValue());
                this.editor.destroy();
            } else {
                // save changes in local context
                value=jsonschema.asObject(jsonschema.jsonschema_body);
            }
            this.isHowto=true
            
            // Initialize the editor
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
                // "button":  function view_info(jseditor_editor, input){
                //         console.log(input);
                // },
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
            };
            this.editor = new JSONEditor(document.getElementById('editor-jsonschema-config'),{
                // Enable fetching schemas via ajax
                ajax: true,
                ajaxBase: new URL('jsonschema/schema/', jsonschema.ckan_url),
//                ajaxCredentials: true

                // The schema for the editor
                schema: schema,

                // Seed the form with a starting value
                startval: value,

                // https://github.com/json-editor/json-editor#css-integration
                // barebones, html (the default), bootstrap4, spectre, tailwind
                theme: 'bootstrap3',
                
                // urn_resolver: (urn, callback) => {
                //         loadSchema(urn)
                //             .then(schema=>{callback(schema);})
                //         return true;
                // },
                //jqueryui, fontawesome3, fontawesome4, fontawesome5, openiconic, spectre
                // iconlib: "spectre",
                iconlib: "fontawesome4",
                //,
                // Disable additional properties
                //no_additional_properties: true,

                // Require all properties by default
                // required_by_default: true,
                // object_layout: "grid",
                //template: "mustache",
                //template: "handlebars",
                show_errors: "always",
                keep_oneof_values: false, // https://github.com/jdorn/json-editor/issues/293
                // show_opt_in: 1
                // disable_edit_json: 0,
                // disable_collapse: 0,
                // disable_properties: 0,
                // disable_array_add: 0,
                // disable_array_reorder: 0,
                // disable_array_delete: 0,
                enable_array_copy: 0,
                // array_controls_top: 0,
                // disable_array_delete_all_rows: 0,
                // disable_array_delete_last_row: 0,
                // prompt_before_delete: 1,
                // lib_aceeditor: 1,
                lib_autocomplete: 1,
                lib_sceditor: 1,
                // lib_simplemde: 0,
                lib_select2: 1,
                // lib_selectize: 0,
                // lib_choices: 0,
                // lib_flatpickr: 0,
                // lib_signaturepad: 0,
                // lib_mathjs: 0,
                // lib_cleavejs: 0,
                // lib_jodit: 1,
                lib_jquery: 1,
                lib_dompurify: 1
            });
            this.editor.on('ready',this.editorReady);
            this.editor.on('change',()=>{

                // Get an array of errors from the validator
                if (!jsonschema.editor || !jsonschema.editor.ready){
                    return;
                }
                // TODO call when instantiate -> refactor to function and call onReady
                var errors = jsonschema.editor.validate();
                

                if (errors && Object.keys(errors).length){
                    html_errors='<div style="height:150px; overflow:auto;" id="outher-error">'+
                            '<table id="inner-error" style="width:100%;">'+
                            '<tr>'+
                                '<th><h2>Path</h2></th>'+
                                '<th><h2>Message</h2></th></tr>'+
                                errors.map(
                                    e=>'<tr><td>'+e.path+'</td><td>'+e.message+'</td></tr>'
                                ).reduce((a,c,i)=>a+c,'')+
                            '</table></div>';   
                    this.editorOnChange({'html':html_errors, 'lock':true});
                }
                else
                    this.editorOnChange({'html':undefined, 'lock':false});

            });
            // TODO call validation when instantiate -> refactor to function
      },
      editorToggle: function (enable=false) {
            if(!this.editor) return;
            if(enable===true || !this.editor.isEnabled()) {
              this.editor.enable(true);
              $('#editor-toggle').html("Lock");

              let status = $('#editor-status-holder');
              status.css("color","green");
              status.html("unlocked");
            }
            else {
              this.editor.disable(false);
              $('#editor-toggle').html("Unlock");

              let status = $('#editor-status-holder');
              status.css("color","red");
              status.html("locked");
            }

      },
      wrap: function(func){
          try {
                func(arguments);
          } catch(err) {
            console.log(err.stack);
          } finally {
            event.preventDefault();
          }
      },
      editorReady: function () {
            jsonschema.editor && jsonschema.editor.ready && jsonschema.editor.validate();
            this.editorToggle(true);
      },
      editorOnChange: function (i) {
            let errors=i.html;
            let lock=i.lock;
            var indicator = $('#editor-error-holder');

            // Not valid
            if(errors) {

                if (lock){
                    // prevent switch between editors (locks buttons)
                    if (this.isHowto){
                        $('#editor-editor').prop('disabled',true);
                    } else {
                        $('#editor-howto').prop('disabled',true);
                    }
                    // lock the save button
                    $('.form-actions [name="save"]').prop('disabled',true);
                    indicator.css("color","red");
                } else {
                    // lock inverted
                    if (this.isHowto){
                        $('#editor-howto').prop('disabled',true);
                    } else {
                        $('#editor-editor').prop('disabled',true);
                    }
                    // lock the save button
                    $('.form-actions [name="save"]').prop('disabled',false);
                    indicator.css("color","black");
                }
                indicator.html(errors);
                                        
                //indicator.textContent = "not valid";
            }
            // Valid
            else {
                // un lock the save button
                $('.form-actions [name="save"]').prop('disabled',false);
                // un lock the toggles
                $('#editor-howto').prop('disabled',false);
                $('#editor-editor').prop('disabled',false);
                indicator.html("<b style='display: inline; color: green;'>valid</b>");
            }
        }
    };
    return jsonschema;
});
