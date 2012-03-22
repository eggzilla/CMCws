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
my $model = $query->param('model') || undef;
my $operation = $query->param('operation') || undef;
my $page = $query->param('page') || undef; 
my $tempdir = $query->param('tempdir') || undef;
my $email=$query->param('email-address')|| undef;
my $input_filename=$query->param('file')|| undef;
my $input_filehandle=$query->upload('file')||undef;
my $input_present = undef;

######TAINT-CHECKS##############################################
#get the current page number
#wenn predict submitted wurde ist page 1
if(defined($page)){
    if($page eq "1"){
	$page = 1;
    }elsif($page eq "2"){
	$page = 2;
    }elsif($page eq "3"){
	$page = 3;
    }
}else{
    $page = 0;
}

if(defined($input_filename)){
    #if the file does not meet requirements we delete it before returning to page=0 for error
    my $name = Digest::MD5::md5_base64(rand);
    $name =~ s/\+/_/g;
    $name =~ s/\//_/g;
    unless(-e "$uploaddir"){
	mkdir("$uploaddir");
    }
    open ( UPLOADFILE, ">$uploaddir/$name" ) or die "$!"; binmode UPLOADFILE; while ( <$input_filehandle> ) { print UPLOADFILE; } close UPLOADFILE;
    my $check_size = -s "$uploaddir/$name";
    my $max_filesize =100000;
    if($check_size < 1){
	print STDERR "cmcws: Uploaded Input file is empty\n";
    }elsif($check_size > $max_filesize){
	print STDERR "cmcws: Uploaded Input file is too large\n";
    }
    #check input file
    my $check=&check_input($name);
    print STDERR "cmcws-Inputcheck: $check\n";
    #set input present to true if input is ok and include filename for further processing, return error message if not
}else{
    print STDERR "cmcws:No input-file provided\n";
    print STDERR "params: @names";
}

if($page==0){
    print $query->header();
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	#Interpolate => 1 allows simple variable reference
	#INTERPOLATE=>1,
	#allows use of relative include path
	#PRE_PROCESS => './javascript/input.js',
	RELATIVE=>1,
				 });
    #If input files have already been uploaded display error message or ask for confirmation of the query
    if($input_present){
	
    }
    
    #render page
    my $file = './template/input.html';
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
	scriptfile => "inputscriptfile",
	stylefile => "inputstylefile"
    };
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
    my $stockholm_alignment_detected=0;
    my $covariance_model_detected=0;
    while(<INPUTFILE>){
	chomp;
	#look for header
	if(/\# STOCKHOLM 1\./ && $stockholm_alignment_detected==0){
	    $stockholm_alignment_detected=1;
	    push(@input_elements,"a");
	}elsif(/INFERNAL\-1 \[1/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    push(@input_elements,"c");
	}
	
	#look for name
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
	}else{
	    push(@input_elements,"cm");
	}
	
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
    
    if(@input_elements>0){
	#$input_element_number=(@input_elements/3);
	#for($i..$input_element_number){
	    
	#}
    }else{
	print STDERR "No covariance models or alignments found in inputfile";
    }
    my $stuff=join("",@input_elements);
    close INPUTFILE;
    return $stuff;
}

sub prepare_input{
    #my @file_lines;
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #while(<INPUTFILE>){
    #    push(@file_lines,$_);
    #}
    #my $joined_file=join("",@file_lines);
}

