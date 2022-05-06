// json preview module
ckan.module('jsonschema', function (jQuery, _) {
    jsonschema = {
        saveToContext: function (workOnBody = jsonschema.workOnBody){
            // prepare info to serialize
            let value = jsonschema.editor.getValue();
            if (workOnBody){
                jsonschema.jsonschemaBody = asObject(value);
            } else {
                jsonschema.jsonschemaOpt = asObject(value);
            }
        },
        getValue: function (workOnBody = jsonschema.workOnBody){
            if (workOnBody){
                value = jsonschema.jsonschemaBody;
            } else {
                value = jsonschema.jsonschemaOpt;
            }
            return asObject(value);
        },
        setValue(path, value) {
            var valueEditor = jsonschema.editor.getEditor(path)
            valueEditor.setValue(value)
        },
        onSubmit: function (event) {
                if (!jsonschema.isEditorReady()) return;

                this.saveToContext();

                // OPT
                let input=$('input[name="' + jsonschema.optKey + '"]')[0];
                input.value=asString(this.jsonschemaOpt);
                // BODY
                input=$('input[name="' + jsonschema.bodyKey + '"]')[0];
                input.value=asString(this.jsonschemaBody);

                this.editorToggle(enable=false);
        },
        dynamicModule: async function (url){

            if (!url){
                return;
            }

            let module;
            try {
                module = await import(jsonschema.ckanUrl+'jsonschema/module/'+url);
                if (module){
                    module.initialize();   
                }
            } catch (error) {
                console.error(error.message);
            }
            return module;
        },
        fetch: async function (path, default_return = {}) {
            var url = new URL(encodeURI(path),jsonschema.ckanUrl);
            if (url.length < 2) {
                console.error('Bad url: '+url);
                return default_return;
            }
            return fetch(url).then(function (request) {
                    if (request.status === 200) {
                        return request.json();
                    } else {
                        console.error('Bad response HTTP code: '+request.status);
                        return default_return;
                    }
                }).catch(function (err) {
                    console.error(err);
                    return default_return;
                });
        },
        ckanUrl: undefined,
        jsonschema_schema: undefined,
        jsonschemaBody: undefined,
        jsonschemaOpt: undefined,
        editor: undefined,
        registryEntry: undefined,
        initialize: async function () {
            var self = this;

            jsonschema.ckanUrl = self.options.ckanUrl;
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
            
            //jsonschema_type
            jsonschema.jsonschema_type = self.options.type;

            // download registry entry for jsonschema_type
            jsonschema.registryEntry = registryEntry = jsonschema.registryEntry ||
                await jsonschema.fetch('jsonschema/registry/' + jsonschema.jsonschema_type);

            // should we use the template instead of the passed body?
            jsonschema.useTemplate = (self.options.useTemplate||"false").toLowerCase() == "true";
            // TODO this should be provided by Jinja
            if (jsonschema.useTemplate){
                template = registryEntry.template ? 
                    jsonschema.fetch('jsonschema/template/' + registryEntry.template) : self.options.body;

                opt_template = registryEntry.opt_template ?
                    jsonschema.fetch('jsonschema/template/' + registryEntry.opt_template) : self.options.opt;
                
                const [body, opt] = await Promise.all([template, opt_template]).catch((err)=>console.error(err)); 

                jsonschema.jsonschemaBody = body||{};
                jsonschema.jsonschemaOpt = opt||{};

            } else {

                jsonschema.jsonschemaBody = self.options.body;
                jsonschema.jsonschemaOpt = self.options.opt;

            }

            // keys to find <input/> fields
            jsonschema.bodyKey = self.options.bodyKey;
            jsonschema.typeKey = self.options.typeKey;
            jsonschema.optKey = self.options.optKey;

            // The current package / resource / view
            jsonschema.dataDict = self.options.dataDict; 

            // are we working on the body? (or opt)
            jsonschema.workOnBody = true;

            // are we using the howTo editor (true) or the AJV (false)?
            jsonschema.usingEditor = true;

            // load module if present
            jsonschema.module = await jsonschema.dynamicModule(registryEntry.module);
                        
            // initialize editor
            jsonschema.reload(
                usingEditor = jsonschema.usingEditor,
                workOnBody = jsonschema.workOnBody,
                wasWorkingOverBody = jsonschema.workOnBody);
        },
        reload: async function (
                usingEditor = jsonschema.usingEditor,
                workOnBody = jsonschema.workOnBody,
                wasWorkingOverBody = jsonschema.workOnBody) {

            registryEntry = jsonschema.registryEntry

            if (workOnBody){
                schema = registryEntry.schema;
                template = registryEntry.template;
            } else {
                schema = registryEntry.opt_schema;
                template = registryEntry.opt_template;
            }

            if (!schema){
                jsonschema.jsonschema_schema = { "type": "object" };
            } else {
                // TODO: why we need this?
                resolution_scope = schema.substring(0, schema.lastIndexOf('/') + 1);

                jsonschema.ajaxBase = new URL(jsonschema.base_schema_path + resolution_scope, jsonschema.ckanUrl);

                jsonschema.jsonschema_schema = await jsonschema.fetch(jsonschema.base_schema_path + schema);
            }
        
            if (usingEditor){
                jsonschema.getEditor(workOnBody, wasWorkingOverBody);
            } else {
                jsonschema.getEditorAce(workOnBody, wasWorkingOverBody);
            }
        },
        getEditorAce: function (workOnBody = jsonschema.workOnBody, wasWorkingOverBody = jsonschema.workOnBody){
            
            
            let schema={
                "type": "string",
                "format": "json",
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
                this.saveToContext(wasWorkingOverBody);
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
                startval: JSON.stringify(jsonschema.getValue(workOnBody), null, 2),

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
                loadSchema: loadSchema(jsonschema.ajaxBase), //from jsonschema_tools
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
                }
            }).finally(()=>{
                this.editor.on('ready',this.editorReady);
                this.editor.on('change',()=>{
                    this.editorOnChange(jsonschema.ajvValidation());
                });
                this.editorToggle(true);
                this.usingEditor=false;
            });
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
        getEditor: function (workOnBody = jsonschema.workOnBody, wasWorkingOverBody = jsonschema.workOnBody){

            let schema = jsonschema.jsonschema_schema;

            if (this.editor && this.editor instanceof window.JSONEditor){
                this.saveToContext(wasWorkingOverBody);
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
                startval: jsonschema.getValue(workOnBody),

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
            this.usingEditor=true;
            // TODO call validation when instantiate -> refactor to function
        },
        editorOptToggle: function () {
            if(!jsonschema.isEditorReady()) return;

            jsonschema.saveToContext(jsonschema.workOnBody);

            $('#editor-opt-toggle').html("Loading ...");

            next = !jsonschema.workOnBody;

            // jsonschema.reload(registryEntry = jsonschema.registryEntry,
            // usingEditor = jsonschema.usingEditor,
            // workOnBody = jsonschema.workOnBody,
            // wasWorkingOverBody = jsonschema.workOnBody
            jsonschema.reload(
                usingEditor = jsonschema.usingEditor,
                workOnBody = next,
                wasWorkingOverBody = jsonschema.workOnBody
                ).then(
                    (res)=>{
                        $('#editor-opt-toggle').html(next?"Options":"Body");
                        jsonschema.workOnBody = next;
                    }
                ).catch(
                    (err)=>{
                        alert('Unable to switch, please contact service desk: ' + err);
                        console.error(err.stack);
                        $('#editor-opt-toggle').html(jsonschema.workOnBody?"Body":"Options");
                    }
                )
        },
        editorToggle: function (enable=false) {
            if(!jsonschema.isEditorReady()) return;
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
        isEditorReady: function () {
            return jsonschema.editor && jsonschema.editor.ready;
        },
        editorReady: function () {
            jsonschema.isEditorReady() && jsonschema.editor.validate();
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
                    if (this.usingEditor){
                        $('#editor-editor').prop('disabled',true);
                    } else {
                        $('#editor-howto').prop('disabled',true);
                    }
                    // lock the save button
                    $('.form-actions [name="save"]').prop('disabled',true);
                    indicator.css("color","red");
                } else {
                    // lock inverted
                    if (this.usingEditor){
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
