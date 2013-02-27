// geo location stuff
// already assumes a lot of OpenLayers stuff

    function cleanRdfToJs(input) {
        var output = input.replace(/\./g, "\\.");
        return output.replace(/\:/g, "\\:");
    }

    function getReDBoxById(redboxId) {
        var cleanId = cleanRdfToJs(redboxId);
        return $("#" + cleanId);
    }

    function getReDBoxByClass(redboxClass) {
        var cleanClass = cleanRdfToJs(redboxClass);
        return $("." + cleanClass);
    }

	function splitGeonamesData(row) {
        var items = row[0].split("::");
        return {
            id: items[0],
            uri: items[1],
            display: items[2],
            north: items[3],
            east: items[4]
        };
    }

    $("#add-location").click(function(){
        getReDBoxById("dc:coverage.vivo:GeographicLocation.0.coords").hide();
    });

    $("#geonamesLookup").live("focus", function(){
        var elem = $(this);
        var portalPath = $('#portalPath').val();
        elem.unautocomplete();
            elem.autocomplete(
                portalPath + "/proxyGet?ns=Geonames&autocomplete=true&fields=id,geonames_uri,display,latitude,longitude",
                {
                    extraParams: {
                        qs: function() {
                            var userInput = elem.val();
                            var commaPos = userInput.indexOf(",");
                            if(commaPos!=-1){
                                userInput = userInput.substring(0,commaPos);
                            }
                            var trimmedInput = $.trim(userInput);
                            return "func=search&format=json&rows=25&q=" + escape(trimmedInput);
                        }
                    },
                    formatItem: function(row) { return splitGeonamesData(row).display; },
                    formatResult: function(row) { return splitGeonamesData(row).display; },
                    width: "40em"
                }).result(function(event, row) {
                    if (row) {
                        var data = splitGeonamesData(row);
                        // Pan OpenLayers Map
                        if (window["openLayersMap"] != null) {
                            window["openLayersMap"].panTo(data.east, data.north, 10);
                        }
                    }
                })
        }).live("blur", function(){
            $(this).search();
        });

    $(".autocomplete-geonames").live("focus", function(){
        var elem = $(this);
        var baseId = elem.attr("id").replace(".rdf:PlainLiteral", "");
        var wktElem = getReDBoxById(baseId+".redbox:wktRaw");
        var portalPath = $('#portalPath').val();
        elem.unautocomplete();
        if(getReDBoxById(baseId+".dc:type").val() == "text" && wktElem.val() == ""){
            elem.autocomplete(
           		portalPath + "/proxyGet?ns=Geonames&autocomplete=true&fields=id,geonames_uri,display,latitude,longitude",
                {
                    extraParams: {
                        qs: function() {
                            var userInput = elem.val();
                            var commaPos = userInput.indexOf(",");
                            if(commaPos!=-1){
                                userInput = userInput.substring(0,commaPos);
                            }
                            return "func=search&format=json&rows=25&q=" + escape(userInput);
                        }
                    },
                    formatItem: function(row) { return splitGeonamesData(row).display; },
                    formatResult: function(row) { return splitGeonamesData(row).display; },
                    width: "40em"
                }).result(function(event, row) {
                    if (row) {
                        var data = splitGeonamesData(row);
                        var coordsElem = getReDBoxById(baseId+".coords");
                        getReDBoxById(baseId+".dc:identifier").val(data.uri);
                        getReDBoxById(baseId+".geo:long").val(data.east);
                        getReDBoxById(baseId+".geo:lat").val(data.north);
                        coordsElem.find(".east").text(data.east);
                        coordsElem.find(".north").text(data.north);
                        coordsElem.show();
                    }
                })
            }
        }).live("blur", function(){
            $(this).search();
        });

    $(".map-link").live("click", function(){
        var p = $(this).parent();
        var baseId = p.attr("id").replace(".coords", "");
        var long = getReDBoxById(baseId+".geo:long").val();
        var lat = getReDBoxById(baseId+".geo:lat").val();
        window["openLayersMap"].panTo(long, lat, 10);
        return false;
    });

    $(".clear-link").live("click", function(){
        var p = $(this).parent();
        var baseId = p.attr("id").replace(".coords", "");
        getReDBoxById(baseId+".dc:identifier").removeAttr("value");
        getReDBoxById(baseId+".geo:long").removeAttr("value");
        getReDBoxById(baseId+".geo:lat").removeAttr("value");
        p.hide();
    });

    var lastTypeValue;
    $(".locationType").live("focus", function() {
        // This is only really useful on the first use of the drop-down
        lastTypeValue = $(this).val();
    }).live("change", function(e){
        var elem = $(this);
        var baseId = elem.attr("id").replace(".dc:type", "");
        var wktElem = getReDBoxById(baseId+".redbox:wktRaw");
        var wktString = wktElem.val();
        // OpenLayers Row
        if (wktString != "") {
            var outElem = getReDBoxById(baseId+".rdf:PlainLiteral");
            var type = elem.val();
            // The alert window causes focus changes... use this temp variable instead
            var lastType = lastTypeValue;
            var output = window["openLayersMap"].mapWktData(wktString, type);
            if (output != null) {
                outElem.val(output);
                // Fix the focus loss from the alert
                lastTypeValue = type;
            } else {
                elem.val(lastType);
                // Fix the focus loss from the alert
                lastTypeValue = lastType;
                return;
            }

        // Legacy input
        } else {
            var uriElem = getReDBoxById(baseId+".dc:identifier");
            if(elem.val() != "text" && uriElem.val() != ""){
                if (confirm("Are you sure you want to clear the Geonames linked location?")) {
                    getReDBoxById(baseId+".rdf:PlainLiteral").val("");
                    $("div[id='"+baseId+".coords'] .clear-link").click();
                } else {
                    $(this).val("text");
                }
            }
        }
    });