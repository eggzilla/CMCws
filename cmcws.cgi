#!/usr/bin/perl 
#Main executable of the cmsearch webserver 
use warnings;
use strict;
use diagnostics;
use utf8;
use File::Copy;
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Cwd;
use Digest::MD5;
use CGI::Carp qw(fatalsToBrowser);
use File::Temp qw/tempdir tempfile/;
use Sys::Hostname;

######################### Webserver machine specific settings ############################################
##########################################################################################################
my $host = hostname;
my $webserver_name = "cmcompare-webserver";
my $source_dir=cwd();
my $server;
#baseDIR points to the tempdir folder
my $base_dir;
if($host eq "erbse"){
    $server="http://localhost:800/cmcws";
    $base_dir ="$source_dir/html";
}elsif($host eq "linse"){
    $server="http://rna.tbi.univie.ac.at/cmcws2";
    $base_dir ="/u/html/cmcws";
}else{
#if we are not on erbse or on linse we are propably on rna.tbi.univie.ac.at anyway
    $server="http://rna.tbi.univie.ac.at/cmcws2";
    $base_dir ="/u/html/cmcws";
}

my $upload_dir="$base_dir/upload";
#sun grid engine settings
my $qsub_location="/usr/bin/qsub";
my $sge_queue_name="web_short_q";
my $sge_error_dir="$base_dir/error";
my $accounting_dir="$base_dir/accounting";
my $sge_log_output_dir="$source_dir/error";
my $sge_root_directory="/usr/share/gridengine";
##########################################################################################################
#Write all Output to file at once
$|=1;
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=100000; #max 100kbyte posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;
#print STDERR "got here 1";
#Reset these absolut paths when changing the location of the requirements
#functions for gathering user input
#require "$source_dir/executables/input.pl";
#functions for calculating of results
#require "$source_dir/executables/calculate.pl";
#funtions for output of results
#require "$source_dir/executables/output.pl";

#TODO get rid of all usages of GET in query, e.g. javascript

######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page 0 input, 1 process, 2 output

my @names = $query->param;
my $mode = $query->param('mode') || undef;
my $page = $query->param('page') || undef;
my $uploaded_file= $query->param('uploaded_file') || undef; 
my $tempdir_input = $query->param('tempdir') || undef;
my $email=$query->param('email-address')|| undef;
my $input_filename=$query->param('file')|| undef;
my $input_result_number=$query->param('result_number')||undef;
my $input_filtered_number=$query->param('filtered_number')||undef;
my $input_cutoff=$query->param('cutoff')||undef;
my $input_filehandle=$query->upload('file')||undef;
my $checked_input_present;
my $provided_input="";
my @input_error;
my $error_message="";
my $tempdir;
my $result_number;
my $filtered_number;
my $cutoff;
######TAINT-CHECKS##############################################
#get the current page number
#wenn predict submitted wurde ist page 1
if(defined($page)){
    if($page eq "0"){
	$page = 0;
    }elsif($page eq "1"){
	$page = 1;
    }elsif($page eq "2"){
	$page = 2;
    }elsif($page eq "3"){
	$page = 3;
    }
    
}else{
    $page = 0;
}

#mode
if(defined($mode)){
    if($mode eq "1"){
	$mode = 1;
    }elsif($mode eq "2"){
	$mode = 2;
    }
}else{
    $mode = 0;
}

#uploaded-file
if(defined($uploaded_file)){
    if(-e "$upload_dir/$uploaded_file"){
	#file exists
    }else{
	print STDERR "cmcws: nonexistent uploaded file has been supplied as parameter\n";
    }
}else{
    $uploaded_file = "";
}

#tempdir
if(defined($tempdir_input)){
    if(-e "$base_dir/$tempdir_input"){
	$tempdir = $tempdir_input;    
    }else{
	print STDERR "cmcws: nonexistent tempdir has been supplied as parameter\n";
    }
}

#resultnumber
if(defined($input_result_number)){
    if(-e "$base_dir/$tempdir_input/result$input_result_number"){
	$result_number=$input_result_number;    
    }else{
	print STDERR "cmcws: nonexistent result_number has been supplied as parameter\n";
    }
}

#input-file
if(defined($input_filename)){
    print STDERR "cmcws: Found upload /n";
    #if the file does not meet requirements we delete it before returning to page=0 for error
    my $name = Digest::MD5::md5_base64(rand);
    $name =~ s/\+/_/g;
    $name =~ s/\//_/g;
    $uploaded_file=$name;
    unless(-e "$upload_dir"){
	mkdir("$upload_dir");
    }
    open ( UPLOADFILE, ">$upload_dir/$name" ) or die "$!"; binmode UPLOADFILE; while ( <$input_filehandle> ) { print UPLOADFILE; } close UPLOADFILE;
    my $check_size = -s "$upload_dir/$name";
    my $max_filesize =1000000;
    if($check_size < 1){
	print STDERR "Uploaded Input file is empty\n";
	push(@input_error,"Uploaded Input file is empty");
    }elsif($check_size > $max_filesize){
	print STDERR "Uploaded Input file is too large\n";
	push(@input_error,"Uploaded Input file is too large");
    }else{
	#check input file
	my $check_array_reference=&check_input($name);
	my @check_array = @$check_array_reference;
	print STDERR "Array checked: @check_array\n";
	#get first element and look for error string
	my $error_string = shift(@check_array);
	#set input present to true if input is ok and include filename for further processing, set error message if not
	if($error_string =~ /^error/){
	    print STDERR "Input error detected: $error_string";
	    my @error_string_split = split(/;/,$error_string);
	    shift(@error_string_split);
	    push(@input_error,@error_string_split);
	    #check_input found errors in the input file, we add them to @input_error
	}else{
	    $checked_input_present=1;
	    my $number_of_models=((@check_array)/2)-1;
	    my $counter=0;
	    for(0..$number_of_models){
		$counter++;
		#todo: continue here - each line should contain number, type of input, name (if present)
		my $type=shift(@check_array);
		my $name=shift(@check_array);
		$provided_input=$provided_input."<p>$counter. $type"." $name </p>";
	    }
	}
    }
    
}else{
    #Submit without file, set error message and request file
    push(@input_error,"No Input file provided");
}
   
if(defined($input_filtered_number)){
    if($input_filtered_number =~ /^\d+/){
	#only numbers = Taxid - preset on form in taxid field
	$filtered_number = $input_filtered_number;
    }#todo:else
}else{
    $filtered_number=10;
}

if(defined($input_cutoff)){
    if($input_cutoff =~ /^\d+/){
	$cutoff = $input_cutoff;
    }#todo:else
}else{
    $cutoff=20;
}
	
################ INPUT #####################################

if($page==0){
    #print $query->header();
    print "Content-type: text/html; charset=utf-8\n\n";
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	RELATIVE=>1
				 });
    my $file = './template/input.html';
    my $input_script_file="inputscriptfile";
    my $disabled_upload_form="";
    my $submit_form="";
    #Three different states of the input page
    if($checked_input_present){
	$file = './template/input2.html';
	if($mode eq "1"){
	    #comparison of one model vs rfam 
	    $input_script_file = "inputstep2scriptfile";
	    $disabled_upload_form="inputstep2mode1disable";
	    $submit_form="inputstep2mode1submit";
	    print STDERR "Reached Page=0 step=2 mode=1\n";
	}elsif($mode eq "2"){
	    #comparison of multiple models with each other 
	    $input_script_file = "inputstep2scriptfile";
	    $disabled_upload_form="inputstep2mode2disable";
	    $submit_form="inputstep2mode2submit";
	    print STDERR "Reached Page=0 step=2 mode=2\n";
	}
    }elsif($mode=="0"){
	print STDERR "Reached Page=0 step=1 mode=0\n";
    }else{
	#Input error
	$input_script_file = "inputerrorscriptfile";
	$error_message=join('/n',@input_error);
	print STDERR "Reached Page=0 step=1 mode=$mode\n";
	print STDERR "Error: @input_error\n";
    }
    
    my $vars = {
	#define global variables for javascript defining the current host (e.g. linse) for redirection
	serveraddress => "$server",
	title => "CMcompare - Webserver - Input form",
	banner => "./pictures/banner.png",
	scriptfile => "$input_script_file",
	stylefile => "inputstylefile",
	mode => "$mode",
	error_message => "$error_message",
	disabled_upload_form => "$disabled_upload_form",
	submit_form => "$submit_form",
	uploaded_file => "$uploaded_file",
	provided_input => "$provided_input"
    };
    #todo taintcheck $uploaded_file and hand it over to input2.html
    #todo: hand over provided_input to input2.html
    #render page
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

################ PROCESSING #####################################

if($page==1){
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	RELATIVE=>1
				 });
    my $file = './template/processing.html';
    my $processing_script_file="processingscriptfile";
    my $error_message="";
    my $query_number="";
    my $number_of_all_rfam_models=1974;
    my $processing_table_content="";
    #Check mode
    #Prepare the input by creating a file for each model
    unless(defined($tempdir)){
	$tempdir = tempdir ( DIR => $base_dir );
	$tempdir =~ s/$base_dir\///;
	chmod 0755, "$base_dir/$tempdir";
    }
    if(-e "$base_dir/$tempdir/query_number"){
	if($mode eq "1"){
	    #each submitted model is compared against rfam
	    open (QUERYNUMBERFILE, "<$base_dir/$tempdir/query_number")or die "Could not create $tempdir/query_number: $!\n";
	    $query_number=<QUERYNUMBERFILE>;
	    close QUERYNUMBERFILE;
	    #assemble 
	    my $counter=1;
	    for(1..$query_number){
		my $query_id=$counter;
		my $queueing_status="";
		my $model_comparison="";
		my $parsing_output="";
		my $result_page_link="";
		if(-e "$base_dir/$tempdir/begin$counter"){$queueing_status="Processing..";}
		elsif(!-e "$base_dir/$tempdir/done$counter") {$queueing_status="Queued";}
		else{$queueing_status="Done";}
		if(-e "$base_dir/$tempdir/result$counter"){
		    my $result_lines=`cat $base_dir/$tempdir/result$counter | wc -l`;
		    my $progress_percentage=($result_lines/$number_of_all_rfam_models)*100;
		    my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage);
		    $model_comparison="Progress: $rounded_progress_percentage%";}
		else {$model_comparison="";}
		if(-e "$base_dir/$tempdir/output"."$counter".".html"){$parsing_output="";} 
		else {$parsing_output="";}
		if(-e "$base_dir/$tempdir/done$counter"){$result_page_link="<a href=\"$server/cmcws.cgi?page=2&mode=$mode&tempdir=$tempdir&result_number=$counter\">Link</a>"; } 
		else{$result_page_link=""}
		
		$processing_table_content=$processing_table_content."<tr><td>$query_id</td><td>$queueing_status</td><td>$model_comparison</td><td>$parsing_output</td><td>$result_page_link</td></tr>";
		$counter++;
	    }
	    
	}elsif($mode eq "2"){
	    #the models are compared againsted each other and optionally additionally against rfam
	    $query_number=1;
	    
	}
    }else{
	$processing_table_content=$processing_table_content."<tr><td>Loading..</td></tr>";
    }
    unless(-e "$base_dir/$tempdir/covariance_model"){
	#add to path or taintcheck will complain
	$ENV{PATH}="$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
	mkdir("$base_dir/$tempdir/covariance_model",0744);
	mkdir("$base_dir/$tempdir/stockholm_alignment",0744);
	open (COMMANDS, ">$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";	
	print COMMANDS "#!/bin/bash\n";
	print COMMANDS "cp $upload_dir/$uploaded_file $base_dir/$tempdir/input_file;\n";
	print COMMANDS "cd $base_dir/$tempdir/;\n";
	print COMMANDS "$source_dir/executables/split_input.pl $base_dir/$tempdir/input_file $base_dir/$tempdir/;\n";
	print COMMANDS "$source_dir/executables/convert_stockholmdir_to_cmdir.pl $base_dir/$tempdir $source_dir;\n";
	print COMMANDS "$source_dir/executables/calculate.pl $base_dir/$tempdir $source_dir $mode;\n";
	#print COMMANDS ";\n";
	if($mode eq "1"){
	    #set stuff specific for mode 1
	}elsif($mode eq "2"){
	    #set stuff specific for mode 2
	}
	#FORK here
	if (my $pid = fork) {
	    $query->delete_all();
	    #send user to result page
	    #redirect
	    #print"<script type=\"text/javascript\">
	    #                        window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);
	    #                        </script>";
	    close COMMANDS; #close COMMANDS so child can reopen filehandle
	}elsif (defined $pid){		
	    close STDOUT;
	    #open (COMMANDS, ">>$base_dir/$tempdir/commands.sh") or die "Could not create commands.sh";
	    #print COMMANDS "touch $base_dir/$tempdir/done;\n";
	    #close COMMANDS;
	    my $ip_adress=$ENV{'REMOTE_ADDR'};
	    $ip_adress=~s/\.//g;
	    my ($sec,$min,$hour,$day,$month,$yr19,@rest) = localtime(time);
	    my $timestamp=(($yr19+1900)."-".sprintf("%02d",++$month)."-".sprintf("%02d",$day)."-".sprintf("%02d",$hour).":".sprintf("%02d",$min).":".sprintf("%02d",$sec));
	    #write report to accounting file
	    open(ACCOUNTING, ">>$base_dir/accounting/accounting") or die "Could not write to accounting file: $!/n";
	    #ipaddress tempdir timestamp mode querynumber
	    print ACCOUNTING "$ip_adress $tempdir $timestamp $mode $query_number\n";
	    close ACCOUNTING;
	    chmod (0755,"$base_dir/$tempdir/commands.sh");
	    exec "export SGE_ROOT=$sge_root_directory; $qsub_location -N IP$ip_adress -q web_short_q -e /scratch2/RNApredator/error -o /scratch2/RNApredator/error $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid" or die "Could not execute sge submit: $! /n";
	}
    }
    my $progress_redirect="<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);    
          </script>";
    my $link="$server/cmcws.cgi?"."page=1"."&tempdir=$tempdir"."&mode=$mode";
    my $vars = {
	#define global variables for javascript defining the current host (e.g. linse) for redirection
	serveraddress => "$server",
	title => "CMcompare - Webserver - Input form",
	banner => "./pictures/banner.png",
	scriptfile => "$processing_script_file",
	stylefile => "inputstylefile",
	mode => "$mode",
	error_message => "$error_message",
	uploaded_file => "$uploaded_file",
	processing_table_content => "$processing_table_content",
	processing_redirect =>"$progress_redirect",
	link => "$link"	    
    };
    print "Content-type: text/html; charset=utf-8\n\n";
    
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

################ OUTPUT #####################################

#We have 2 different output pages: overview page for the comparison of several models with each other(mode1)
#detailed page for the comparison of one model vs rfam(mode2)

if($page==2){
    #output
    print "Content-type: text/html; charset=utf-8\n\n";
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	RELATIVE=>1
				 });
    my $output_script_file="outputscriptfile";
    my $total;
    if($mode eq "1"){
	$total=1974+$result_number;
    }else{
	#todo:set for mode 2
}
    my $error_message="";
    my $vars;
    my $file;
    #Check mode
    if($mode eq "1"){
	if(-e "$base_dir/$tempdir/done$result_number"){	
	    #each submitted model is compared against rfam
	    $file = './template/output.html';
	    $output_script_file="outputscriptfile";
	    $vars = {
		#define global variables for javascript defining the current host (e.g. linse) for redirection
		serveraddress => "$server",
		title => "CMcompare - Webserver - Input form",
		banner => "./pictures/banner.png",
		scriptfile => "$output_script_file",
		stylefile => "inputstylefile",
		mode => "$mode",
		filtered=> "$filtered_number",
		total=> "$total",
		cutoff=> "$cutoff",
		error_message => "$error_message"
	    };
	    print STDERR "cmcws: Page:2 Mode:1 reached/n";
	}else{
	    print "<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);    
          </script>\n";
	    #todo add errormessage that results are not yet available
	}
    }elsif($mode eq "2"){
	#the models are compared againsted each other and optionally additionally against rfam
	#display the overview page
	if(-e "$base_dir/$tempdir/done"){	
	    #each submitted model is compared against rfam
	    $file = './template/output.html';
	    $output_script_file="outputscriptfile";
	    $vars = {
		#define global variables for javascript defining the current host (e.g. linse) for redirection
		serveraddress => "$server",
		title => "CMcompare - Webserver - Input form",
		banner => "./pictures/banner.png",
		scriptfile => "$output_script_file",
		stylefile => "inputstylefile",
		mode => "$mode",
		error_message => "$error_message"
	    };
	    print STDERR "cmcws: Page:2 Mode:2 reached/n";
	}else{
	    print "<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);    
          </script>\n";
	    #todo add errormessage that results are not yet available
	}
    }else{
	print STDERR "cmcws: Mode not set on outputpage";
    }
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

################ POST-PROCESSING ############################

if($page==3){
    #postprocessing
}


#############################################################

sub check_input{
    #Parameter is filename
    #File can contain multiple cm or alignments in stockholm format
    #Begin of a stockholm-alignment is denoted by:  # STOCKHOLM 1.0
    #Begin of a cm is denoted by: INFERNAL-1 [1.0]
    #End of a stockholm or cm file from rfam is denoted by: //
    my $input_filename=shift;
    open (INPUTFILE, "<$upload_dir/$input_filename") or die "Cannot open input-file";
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #input_elements contains the type of input, the name and the accession number
    my @input_elements;
    #We expect a error by default and set this return value to ok if the input fits
    push(@input_elements,"error;");
    my $stockholm_alignment_detected=0;
    my $covariance_model_detected=0;
    my $counter=0;
    
    while(<INPUTFILE>){
	chomp;
	#look for header
	if(/\# STOCKHOLM 1\./ && $stockholm_alignment_detected==0){
	    $stockholm_alignment_detected=1;
	    push(@input_elements,"Stockholm alignment -");
	    $counter++;
	}elsif(/INFERNAL\-1 \[1/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    push(@input_elements,"Covariance model -");
	    $counter++;
	}
	
	#look for name
	#todo: set default name if we hit end of alignment/cm and do not detect name 
	if(/^\#\=GF\sID/ && $stockholm_alignment_detected==1){
	    $stockholm_alignment_detected=2;
	    my @split_array = split(/\s+/,$_);
	    my $last_element = @split_array - 1;
	    my $name=$split_array[$last_element];
	    push(@input_elements,$name);
	}elsif(/^NAME/ && $covariance_model_detected==1){
	    $covariance_model_detected=2;
	    my @split_array = split(/\s+/,$_);
	    my $last_element = @split_array - 1;
	    my $name=$split_array[$last_element];
	    push(@input_elements,$name);
	}
	#we hit end of model without finding a name
	if(/^\/\// && ($stockholm_alignment_detected==1 || $covariance_model_detected==1 )){
	    push(@input_elements,"unnamed");
	    $stockholm_alignment_detected=0;
	    $covariance_model_detected=0;
	}
	if(/^\/\// && ($stockholm_alignment_detected==2 || $covariance_model_detected==2 )){
	    $stockholm_alignment_detected=0;
	    $covariance_model_detected=0;
	}
    }
    
    if(@input_elements>2){
	#input 
	my $input_element_count=@input_elements;
	my $unexpected_number_of_input_elements=($input_element_count-1)%2;
	print STDERR "cmcws: Number of input element: $input_element_count, Erwartete Anzahl an Elementen gefunden: $unexpected_number_of_input_elements";
	#todo: set default name if we do not find one or this step is problematic
	if((($input_element_count-1)%2)==0){
	    #contains models
	    $input_elements[0]="true";
	}
	print STDERR "cmcws: contains models\n";
    }else{
	#No covariance models or alignments found in input
	$input_elements[0]=$input_elements[0]."No covariance models or alignments found in input<br>;";
    }   
    close INPUTFILE;
    return \@input_elements;
}
