// part of jsonschema module
ckan.module('jsonschema_tools', function (jQuery, _) {
    /* Check if string is valid UUID */
    isValidUUID = (str) => {
        // Regular expression to check if string is a valid UUID
        const regexExp = /^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/gi;
        return regexExp.test(str);
    };

    loadSchema = (base_url) => function (uri) {
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
                return get(retry,new URL(uri, base_url));
            }
        });
    };
    asObject = function (value) {
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
    };

    asString = function (value) {
        if (value){
            if (typeof value == "string"){
                return value;
            } else {
                return JSON.stringify(value, null, '  ');
            }
        }
        return "";
    };
    
    wrap = function(func){
        try {
            func(arguments);
        } catch(err) {
        console.log(err.stack);
        } finally {
        event.preventDefault();
        }
    };
    
});
