/////////////////////////////////////////////////////////////////////////////
///////////////Cross Browser Code for Tooltips /////////////////////////////
(function(window, document, undefined){
    var XBTooltip = function( element, userConf, tooltip) {
	var config = {
            id: userConf.id|| undefined,
            className: userConf.className || undefined,
            x: userConf.x || 20,
            y: userConf.y || 20,
            text: userConf.text || undefined
	};
	var over = function(event) {
            tooltip.style.display = "block";
	},
	out = function(event) {
            tooltip.style.display = "none";
	},
	move = function(event) {
            event = event ? event : window.event;
            if ( event.pageX == null && event.clientX != null ) {
		var doc = document.documentElement, body = document.body;
		event.pageX = event.clientX + (doc && doc.scrollLeft || body && body.scrollLeft || 0) - (doc && doc.clientLeft || body && body.clientLeft || 0);
		event.pageY = event.clientY + (doc && doc.scrollTop  || body && body.scrollTop  || 0) - (doc && doc.clientTop  || body && body.clientTop  || 0);
            }
            tooltip.style.top = (event.pageY+config.y) + "px";
            tooltip.style.left = (event.pageX+config.x) + "px";
	}
	if (tooltip === undefined && config.id) {
            tooltip = document.getElementById(config.id);
            if (tooltip) tooltip = tooltip.parentNode.removeChild(tooltip)
	}
	if (tooltip === undefined && config.text) {
            tooltip = document.createElement("div");
            if (config.id) tooltip.id= config.id;
            tooltip.innerHTML = config.text;
	}
	if (config.className) tooltip.className = config.className;
	tooltip = document.body.appendChild(tooltip);
	tooltip.style.position = "absolute";
	element.onmouseover = over;
	element.onmouseout = out;
	element.onmousemove = move;
	over();
    };
    window.XBTooltip = window.XBT = XBTooltip;
})(this, this.document);


function reseter(ref){
    //alert("reset");
    var server_address=document.getElementById("server_address").innerHTML;
    window.location = server_address + "/cmcws.cgi";	
    // send reload header?
    
}

///////////////////////////////////////////////////////////////////////////////////
/////////////Process cm vs cm input///////////////////////////////////////////////

function step1_operation(ref){
    var selected_operation=document.getElementById("select_operation").value;
    var code="";
    var search=/Rfam/g;
    var operation1_selected=search.test(selected_operation);
    if(operation1_selected==true){
	code ="<div id=\"validation_message\"></div>"+
	    "Upload a covariance model<br>"+
	    "or a multiple alignment <a href=\"#\" onmouseover=\"XBT(this, {id:'2'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a>:<br>"+
	    "<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">" +
            "<br><input name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
            "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +
	    "<input id=\"mode\" value=\"1\"  name=\"mode\" type=\"hidden\"  maxlength=\"1\">" +
            "<br><input type=\"submit\" value=\"Submit\">"+
            "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
            "</form>";
    }else{
	code ="<div id=\"validation_message\"></div>"+
	    "Upload an archive containing a group of<br>"+
	    "multiple alignments or covariance models <a href=\"#\" onmouseover=\"XBT(this, {id:'3'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a>:<br>"+
	    "<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">" +
            "<br><input name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
            "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +
	    "<input id=\"mode\" value=\"2\"  name=\"mode\" type=\"hidden\"  maxlength=\"1\">" +
            "<br><input type=\"submit\" value=\"Submit\">"+
            "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
            "</form>";
    }
    var myText=document.createTextNode(code);
    //hide buttons from 1st step and disable eventhandlers
    document.getElementById("select_operation").disabled=true;
    //set new stuff
    document.getElementById("step1_2_content").innerHTML=code
}