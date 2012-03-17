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
my $model1 = $query->param('model1') || undef;
my $model2 = $query->param('model1') || undef;
my $operation = $query->param('operation') || undef; 
my $page = $query->param('page') || undef; 
my $tempdir = $query->param('tempdir') || undef;
my @names = $query->param;
my $email=$query->param('email-address')|| undef;

######TAINT-CHECKS##############################################
#get the current page number
#wenn predict submitted wurde ist page 1
if(defined($page)){
	if($page eq 1){
		$page = 1;
	}elsif($page eq 2){
		$page = 2;
	}elsif($page eq 3){
		$page = 3;
	}
}else{
	$page = 0;
}
#print STDERR "Got here 2 - taint check - Page: $page";
#TODO:write missing taint-checks

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

	my $file = './template/input.html';
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    #define global varibales for javascript defining the current host (e.g. linse) for redirection
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
