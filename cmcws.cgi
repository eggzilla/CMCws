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
use Bio::SeqIO;
use Cwd;
use Digest::MD5;
use CGI::Carp qw(fatalsToBrowser);
use File::Temp qw/tempdir tempfile/;
######################### Webserver machine specific settings ############################################
##########################################################################################################
my $webserver_name = "cmcompare-webserver";
my $server="http://localhost:800/cmcws";
my $source_dir=cwd();
#baseDIR points to the tempdir folder
my $base_dir ="$source_dir/html";
my $uploaddir="$base_dir/upload";
#sun grid engine settings
my $qsub_location="/usr/bin/qsub";
my $sge_queue_name="web_short_q";
my $sge_error_dir="$source_dir/error";
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

######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page if=0 then input, if=1 then calculate and if=2 then output
#available_genomes can call RNApredator via CGI therfore
#$tax_id has to be taintchecked
my @names = $query->param;
my $mode = $query->param('mode') || undef;
my $page = $query->param('page') || undef;
my $uploaded_file= $query->param('uploaded_file') || undef; 
my $tempdir = $query->param('tempdir') || undef;
my $email=$query->param('email-address')|| undef;
my $input_filename=$query->param('file')|| undef;
my $input_filehandle=$query->upload('file')||undef;
my $checked_input_present;
my $provided_input="";
my @input_error;
my $error_message="";

#print STDERR "cmcws: Debug-start: mode - $mode, page - $page, filename - $input_filename\n";
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
    if(-e "$uploaddir/$uploaded_file"){
	#file exists
        }
}else{
    $uploaded_file = "";
}


#input-file
if(defined($input_filename)){
    print STDERR "cmcws: Found upload /n";
    #if the file does not meet requirements we delete it before returning to page=0 for error
    my $name = Digest::MD5::md5_base64(rand);
    $name =~ s/\+/_/g;
    $name =~ s/\//_/g;
    $uploaded_file=$name;
    unless(-e "$uploaddir"){
	mkdir("$uploaddir");
    }
    open ( UPLOADFILE, ">$uploaddir/$name" ) or die "$!"; binmode UPLOADFILE; while ( <$input_filehandle> ) { print UPLOADFILE; } close UPLOADFILE;
    my $check_size = -s "$uploaddir/$name";
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
	    print STDERR "Input error detected";
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

if($page==0){
    print $query->header();
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
	model_comparison => "cmcws.cgi",
	introduction => "introduction.html",
	available_genomes => "available_genomes.cgi",
	target_search => "target_search.cgi",
	help => "help.html",
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

if($page==1){

}
if($page==2){

}

sub check_input{
    #Parameter is filename
    #File can contain multiple cm or alignments in stockholm format
    #Begin of a stockholm-alignment is denoted by:  # STOCKHOLM 1.0
    #Begin of a cm is denoted by: INFERNAL-1 [1.0]
    #End of a stockholm or cm file from rfam is denoted by: //
    my $input_filename=shift;
    open (INPUTFILE, "<$uploaddir/$input_filename") or die "Cannot open input-file";
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
	#todo: error if we detected a header or a name but no end (//)
	if(/^\/\// && ($stockholm_alignment_detected==2 || $covariance_model_detected==2 )){
	    $stockholm_alignment_detected=0;
	    $covariance_model_detected=0;
	    #todo we should not push this at all, but throw an error
	}
	    	
    }
    
    if(@input_elements>2){
	#input 
	my $input_element_count=@input_elements;
	my $unexpected_number_of_input_elements=($input_element_count-1)%2;
	print STDERR "cmcws: Anzahl der Input-Elemente: $input_element_count, Erwartete Anzahl an Elementen gefunden: 	$unexpected_number_of_input_elements";
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

sub prepare_input{
    #my @file_lines;
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #while(<INPUTFILE>){
    #    push(@file_lines,$_);
    #}
    #my $joined_file=join("",@file_lines);

    	#look for accession number
	#=GF AC   RF00001
	#=GF ID   5S_rRNA
	#if(/^\#\=GF\sAC//^ACCESSION/ && $stockholm_alignment_detected==2){
	#    $stockholm_alignment_detected=0;
	#    my @split_array = split(/\s+/,$_);
	#    my $last_element = @split_array - 1;
	#    my $accession=$split_array[$last_element];
	#    push(@input_elements,$accession);
	#}elsif(/^ACCESSION/ && $covariance_model_detected==2){
	#    $covariance_model_detected=0;
	#    my @split_array = split(/\s+/,$_);
	#    my $last_element = @split_array - 1;
	#    my $accession=$split_array[$last_element];
	#    push(@input_elements,$accession);
	#}else{
	#    
	#}
}

