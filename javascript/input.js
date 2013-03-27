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
	    "Upload a file containing covariance models<br>"+
	    "or multiple alignments <a href=\"#\" onmouseover=\"XBT(this, {id:'2'})\"><img style=\"vertical-align:middle;border:0;\" alt=\"info\" src=\"pictures/info.png\"></a>:<br>"+
	    "<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">" +
            "<br><input name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
            "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\">" +
	    "<input id=\"mode\" value=\"1\"  name=\"mode\" type=\"hidden\">" +
            "<br><input type=\"submit\" value=\"Submit\">"+
            "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
            "</form>";
    }else{
	code ="<div id=\"validation_message\"></div>"+
	    "Upload a file containing covariance models<br>"+
	    "or multiple alignments <a href=\"#\" onmouseover=\"XBT(this, {id:'3'})\"><img style=\"vertical-align:middle;border:0;\" alt=\"info\" src=\"pictures/info.png\"></a>:<br>"+
	    "<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">" +
            "<br><input name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
            "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\">" +
	    "<input id=\"mode\" value=\"2\"  name=\"mode\" type=\"hidden\">" +
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

////////////////////Paste sample for mode 1//////////////////////////////////////

function sample_mode1(){
    var code="<table style=\"border-width:0\">"+
	"<tbody>"+
	"<tr>"+
      "<td id=\"step1_title\"><u>1. Input:</u></td>"+
      "<td id=\"step2_title\"><u>2. Confirm & Submit:</u></td>"+
    "</tr>"+
    "<tr>"+		
      "<td id=\"step1_content\" >"+
	"<form action=\"/cgi-bin/cmcws.cgi\" method=\"post\" target=\"Daten\">"+
	  "<p>Select type of comparison: <a href=\"#\" onmouseover=\"XBT(this, {id:'1'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a></p>"+
	  "<p><select disabled id=\"select_operation\"  onchange=\"step1_operation(this)\">"+
	      "<option>Please select</option>"+
	      "<option>covariance model vs Rfam</option>"+
	      "<option>covariance model vs covariance model</option>"+
	    "</select>"+
	  "</p>"+
	"</form>"+
      "</td>"+
      "<td id=\"step2_content\" style=\"vertical-align:top\">"+
	"You have provided following input:<br>"+
	"<br>1. Covariance model - tRNA<br><br>"+
      "</td>"+
    "</tr>"+	
    "<tr>"+
      "<td id=\"step1_2_content\" style=\"vertical-align:top\">"+
		"<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">"+
	"Upload a covariance model<br>"+
	"or a multiple alignment <a href=\"#\" onmouseover=\"XBT(this, {id:'2'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a>:<br>"+
        "<br><input disabled name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
        "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\">"+
	"<input id=\"mode\" value=\"1\"  name=\"mode\" type=\"hidden\">"+
        "<div id=\"file_message\" style=\"color: red;\"></div>"+
        "<br>"+
        "<br>"+
        "</form>"+
      "</td>"+
      "<td id=\"step2_2_content\" style=\"vertical-align:top\">"+
		"<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">"+
	"Which part of Rfam do you want to compare against?<br>"+
	"<select id=\"select_slice\" size=\"3\" name=\"select_slice\">"+
	"<option selected>All</option>"+
	"<option>Gene</option>"+
	"<option>CRISPR</option>"+
	"<option>antisense</option>"+
	"<option>antitoxin</option>"+
	"<option>lncRNA</option>"+
	"<option>microRNA</option>"+
	"<option>rRNA</option>"+
	"<option>ribozyme</option>"+
	"<option>sRNA</option>"+
	"<option>snRNA</option>"+
	"<option>snoRNA</option>"+
	"<option>CD-box</option>"+
	"<option>HACA-box</option>"+
	"<option>scaRNA</option>"+
	"<option>splicing</option>"+
	"<option>tRNA</option>"+
	"<option>Intron</option>"+
	"<option>Cis-reg</option>"+
	"<option>IRES</option>"+
	"<option>frameshift element</option>"+
	"<option>riboswitch</option>"+
	"<option>thermoregulator</option>"+
	"<option>leader</option>"+
	"</select>"+
	"<br>"+
	"<br>"+
        "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\">"+
	"<input id=\"mode\" value=\"1\"  name=\"mode\" type=\"hidden\">"+
	"<input id=\"uploaded_file\" value=\"sample_mode_1\"  name=\"uploaded_file\" type=\"hidden\">"+
	"Note: Comparison takes minutes to hours<br>"+
	"<input type=\"submit\" value=\"Compare\">"+
        "<input type=\"button\" value=\"Back\" onclick=\"back(this)\">"+
        "</form>"+
      "</td>"+
    "</tr>"+
      "<tr>"+
      "<td id=\"step1_3_content\" style=\"vertical-align:top\">"+
      "</td>"+
      "<td id=\"step2_3_content\" style=\"vertical-align:top\">"+
	"<div id=\"error_message\"> </div>"+
      "</td>"+
    "</tr>"+
	"</tbody>"+
    "</table>";
    var myText=document.createTextNode(code);
    document.getElementById("input_table").innerHTML=code;
}

function sample_mode2(){
    var code="<table>"+
        "<tbody>"+
	"<tr>"+
    "<td id=\"step1_title\"><u>1. Input:</u></td>"+
    "<td id=\"step2_title\"><u>2. Confirm & Submit:</u></td>"+
    "</tr>"+
    "<tr>"+		
      "<td id=\"step1_content\">"+
	"<form action=\"/cgi-bin/cmcws.cgi\" method=\"post\" target=\"Daten\">"+
	  "<p>Select type of comparison: <a href=\"#\" onmouseover=\"XBT(this, {id:'1'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a></p>"+
	  "<p><select disabled id=\"select_operation\"  onchange=\"step1_operation(this)\">"+
	      "<option>Please select</option>"+
	      "<option>covariance model vs Rfam</option>"+
	     "<option>covariance model vs covariance model</option>"+
	   "</select>"+
	 "</p>"+
	"</form>"+
      "</td>"+	
      "<td id=\"step2_content\" style=\"vertical-align:top\">"+
	"You have provided following input:<br>"+
	"<br>1. Covariance model - tRNA<br>2. Covariance model - tmRNA<br>3. Covariance model - alpha_tmRNA<br>4. Covariance model - beta_tmRNA<br>5. Covariance model - cyano_tmRNA<br>6. Covariance model - tRNA-Sec<br><br>"+
      "</td>"+
    "</tr>"+	
    "<tr>"+
      "<td id=\"step1_2_content\" style=\"vertical-align:top\">"+
	"<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">"+
	"Upload an archive containing a group of<br>"+
	"multiple alignments or covariance models "+
	"<a href=\"#\" onmouseover=\"XBT(this, {id:'3'})\"><img style=\"vertical-align:middle\" src=\"pictures/info.png\" border=\"0\"></a>:<br>"+
        "<br><input disabled name=\"file\" id=\"file\" size=\"30\" type=\"file\"><br>"+
        "<input id=\"page\" value=\"0\"  name=\"page\" type=\"hidden\">"+
	"<input id=\"mode\" value=\"2\"  name=\"mode\" type=\"hidden\">"+
        "<div id=\"file_message\" style=\"color: red;\"></div>"+
        "<br>"+
	"<br>"+
        "</form>"+
      "</td>"+
      "<td id=\"step2_2_content\" style=\"vertical-align:top\">"+
		"<form action=\"cmcws.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">"+
	"Note: Comparison takes minutes to hours"+
	"<br>"+
	"<br>"+
        "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\">"+
	"<input id=\"mode\" value=\"2\"  name=\"mode\" type=\"hidden\">"+
	"<input id=\"uploaded_file\" value=\"mode2.cm\"  name=\"uploaded_file\" type=\"hidden\">"+
	"<input type=\"submit\" value=\"Compare\">"+
        "<input type=\"button\" value=\"Back\" onclick=\"back(this)\">"+
        "</form>"+
      "</td>"+
    "</tr>"+
      "<tr>"+
      "<td id=\"step1_3_content\" style=\"vertical-align:top\">"+
      "</td>"+
      "<td id=\"step2_3_content\" style=\"vertical-align:top\">"+
	"<div id=\"error_message\"> </div>"+
      "</td>"
    "</tr>"+
    "</tbody>"+
    "</table>";
    var myText=document.createTextNode(code);
    document.getElementById("input_table").innerHTML=code;
}
