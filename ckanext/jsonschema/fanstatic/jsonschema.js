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
                return get(retry, new URL(uri, jsonschema.ajaxBase));
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
        saveToContext: function (work_over_body = jsonschema.work_over_body){
            // prepare info to serialize
            let value = jsonschema.editor.getValue();
            if (work_over_body){
                jsonschema.jsonschema_body = jsonschema.asObject(value);
            } else {
                jsonschema.jsonschema_opt = jsonschema.asObject(value);
            }
        },
        getValue: function (work_over_body = jsonschema.work_over_body){
            if (work_over_body){
                value = jsonschema.jsonschema_body;
            } else {
                value = jsonschema.jsonschema_opt;
            }
            return jsonschema.asObject(value);
        },
        onSubmit: function (event) {
                if (!this.editor) return;

                this.saveToContext();

                // opt
                let input=$('input[name="' + jsonschema.optKey + '"]')[0];
                input.value=jsonschema.asString(this.jsonschema_opt);
                // BODY
                input=$('input[name="' + jsonschema.bodyKey + '"]')[0];
                input.value=jsonschema.asString(this.jsonschema_body);

                this.editorToggle(enable=false);
        },
        dynamic_module: async function (url){

            if (!url){
                return;
            }

            let module;
            try {
                module = await import(jsonschema.ckan_url+'jsonschema/module/'+url);
                if (module){
                    module.initialize();   
                }
            } catch (error) {
                console.error(error.message);
            }
            return module;
        },
        fetch: function (path) {
            var url = new URL(encodeURI(path),jsonschema.ckan_url);
            if (url.length < 2) {
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
        },
        ckan_url: undefined,
        jsonschema_schema: undefined,
        jsonschema_body: undefined,
        jsonschema_opt: undefined,
        editor: undefined,
        initialize: function () {
            var self = this;

            jsonschema.ckan_url = self.options.ckanUrl;
            jsonschema.base_schema_path = 'jsonschema/schema/';
            jsonschema.reload=this.reload.bind(jsonschema);
            jsonschema.getEditor=this.getEditor.bind(jsonschema);
            jsonschema.getEditorAce=this.getEditorAce.bind(jsonschema);
            jsonschema.editorReady=this.editorReady.bind(jsonschema);
            jsonschema.editorValidate=this.editorReady.bind(jsonschema);
            jsonschema.editorToggle=this.editorToggle.bind(jsonschema);

            // form onSubmit binding to json-editor submit event
            $('.dataset-form').find('button[type=submit]').each(
                function (){$(this).on('click', jsonschema.onSubmit.bind(jsonschema));});

            // initialize previous value (from jinja2 dataset form)

            //TODO if schema changes, use_template should be false (jsonschema_schema != options.schema)
            
            jsonschema.jsonschema_type = self.options.type;
            jsonschema.jsonschema_body = self.options.body;
            jsonschema.jsonschema_opt = self.options.option;
            jsonschema.use_template = (self.options.useTemplate||"false").toLowerCase() == "true";
            jsonschema.bodyKey = self.options.bodyKey;
            jsonschema.typeKey = self.options.typeKey;
            jsonschema.optKey = self.options.optKey;
            jsonschema.element = self.options.element; //this will be the full current package/resource/view

            jsonschema.work_over_body = true;
            jsonschema.use_editor = true;
            
            // initialize editor
            
            jsonschema.reload(jsonschema.jsonschema_type, 
                use_editor = jsonschema.use_editor,
                use_template = jsonschema.use_template,
                work_over_body = jsonschema.work_over_body);
        },
        reload: async function (jsonschema_type,
            use_editor = jsonschema.use_editor,
            use_template = jsonschema.use_template,
            work_over_body = jsonschema.work_over_body,
            was_working_over_body = jsonschema.work_over_body
            ) {

            jsonschema.jsonschema_type = jsonschema_type;

            registry_entry = await jsonschema.fetch('jsonschema/registry/' + jsonschema_type);

            if (work_over_body){
                schema = registry_entry.schema;
                template = registry_entry.template;
            } else {
                schema = registry_entry.opt_schema;
                template = registry_entry.opt_template;
            }

            if (!schema){
                jsonschema.jsonschema_schema = {
                    "type": "object"
                };
            } else {
                // TODO: why we need this?
                resolution_scope = schema.substring(0, schema.lastIndexOf('/')+1);

                jsonschema.ajaxBase = new URL(jsonschema.base_schema_path + resolution_scope, jsonschema.ckan_url);

                jsonschema.jsonschema_schema = await jsonschema.fetch('jsonschema/schema/' + schema);
            }
            
            jsonschema.module = await jsonschema.dynamic_module(registry_entry.module);
            
            if (use_template){
                if (template){
                    fetched_template = await jsonschema.fetch('jsonschema/template/' + template);
                } else {
                    fetched_template = {};
                    console.warn('No template found for type: ' + template);
                }
                if (work_over_body){
                    jsonschema.jsonschema_body = fetched_template;
                } else {
                    jsonschema.jsonschema_opt = fetched_template;
                }
            }
            if (use_editor){
                jsonschema.getEditor(work_over_body, was_working_over_body);
            } else {
                jsonschema.getEditorAce(work_over_body, was_working_over_body);
            }        
        },
        getEditorAce: function (work_over_body = jsonschema.work_over_body, was_working_over_body = jsonschema.work_over_body){
            this.isHowto=false
            
            let schema={
                "type": "string",
                "format": "json",
                "title": "Body",
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

            if (this.editor && this.editor instanceof window.JSONEditor){
                this.saveToContext(was_working_over_body);
                this.editor.destroy();
            }
            
            // Initialize the editor
            this.editor = new JSONEditor(document.getElementById('editor-jsonschema-config'),{
                // Enable fetching schemas via ajax
                ajax: true,
                ajaxBase: jsonschema.ajaxBase,
//                ajaxCredentials: true

                // The schema for the editor
                schema: schema,

                // Seed the form with a starting value
                startval: jsonschema.getValue(work_over_body),

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
                //strict: false,
                // // allErrors: true,
                // validateSchema: false, 
                strictSchema: false
            });

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
        getEditor: function (work_over_body = jsonschema.work_over_body, was_working_over_body = jsonschema.work_over_body){
            this.isHowto=true

            let schema = jsonschema.jsonschema_schema;

            if (this.editor && this.editor instanceof window.JSONEditor){
                this.saveToContext(was_working_over_body);
                this.editor.destroy();
            }
            
            // Initialize the editor
            this.editor = new JSONEditor(document.getElementById('editor-jsonschema-config'),{
                // Enable fetching schemas via ajax
                ajax: true,
                ajaxBase: jsonschema.ajaxBase,
//                ajaxCredentials: true

                // The schema for the editor
                schema: schema,

                // Seed the form with a starting value
                startval: jsonschema.getValue(work_over_body),

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
        editorOptToggle: function () {
            if(!this.editor) return;

            jsonschema.saveToContext(jsonschema.work_over_body);

            $('#editor-opt-toggle').html("Loading ...");

            next = !jsonschema.work_over_body;

            jsonschema.reload(jsonschema.jsonschema_type, 
                use_editor = jsonschema.isHowto,
                use_template = jsonschema.use_template,
                work_over_body = next,
                was_work_over_body = jsonschema.work_over_body
                ).then(
                    (res)=>{
                        $('#editor-opt-toggle').html(next?"Options":"Body");
                        jsonschema.work_over_body = next;
                    }
                ).catch(
                    (err)=>{
                        alert('Unable to switch, please contact service desk: ' + err);
                        console.error(err.stack);
                        $('#editor-opt-toggle').html(jsonschema.work_over_body?"Options":"Body");
                    }
                )
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
                $('#editor-opt-toggle').prop('disabled',true);

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
                $('#editor-opt-toggle').prop('disabled',false);
                indicator.html("<b style='display: inline; color: green;'>valid</b>");
            }
        }
    };
    return jsonschema;
});
