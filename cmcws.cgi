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
use List::Util qw[min max];
use List::MoreUtils qw[uniq];
######################### Webserver machine specific settings ############################################
##########################################################################################################
my $host = hostname;
my $webserver_name = "cmcompare-webserver";
#my $source_dir=cwd();
my $source_dir="/mnt/storage/progs/cmcws";
#URL of cgi script
my $server;
#URL of static content
my $server_static;
#baseDIR points to the tempdir folder
my $base_dir;
my $rnalien_tmp_dir ="";
if($host eq "erbse"){
    $server = "http://localhost/cmcws";
    #$server="http://131.130.44.243/cmcws";
    $base_dir = "$source_dir/html";
}elsif($host eq "linse"){
    $server = "http://rna.tbi.univie.ac.at/cmcws2";
    $base_dir ="/u/html/cmcws";
}elsif($host eq "lingerie"){
    $server="http://lingerie.tbi.univie.ac.at/cgi-bin/cmcws/cmcws.cgi";
    $server_static = "http://lingerie.tbi.univie.ac.at/cmcws";
    $source_dir = "/mnt/storage/progs/cmcws";
    $base_dir = "$source_dir/html";
}elsif($host eq "nibiru"){
    $server = "http://nibiru.tbi.univie.ac.at/cgi-bin/cmcws/cmcws.cgi";
    $server_static = "http://nibiru.tbi.univie.ac.at/cmcws";
    $source_dir = "/mnt/storage/progs/cmcws";
    $base_dir = "$source_dir/html";
    $rnalien_tmp_dir = "/mnt/storage/tmp/rnalien/";
}else{
#if we are not on erbse or on linse we are propably on rna.tbi.univie.ac.at anyway
    $server = "http://rna.tbi.univie.ac.at/cgi-bin/cmcws/cmcws.cgi";
    $base_dir = "$source_dir/html";
    $source_dir = "/mnt/storage/progs/cmcws";
    $server_static = "http://rna.tbi.univie.ac.at/cmcws";
}

print STDERR "Hostname: $host\n";

my $upload_dir = "$base_dir/upload";
#sun grid engine settings
my $qsub_location = "/usr/bin/qsub";
my $sge_queue_name = "web_long_q";
my $sge_error_dir = "$base_dir/error";
my $accounting_dir = "$base_dir/accounting";
my $sge_log_output_dir = "$source_dir/error";
my $sge_root_directory = "/usr/share/gridengine";
##########################################################################################################
#Write all Output to file at once
$|=1;
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=1500000; #max 100kbyte posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;
#Reset these absolut paths when changing the location of the requirements
#functions for gathering user input
#require "$source_dir/executables/input.pl";
#functions for calculating of results
#require "$source_dir/executables/calculate.pl";
#functions for output of results
#require "$source_dir/executables/output.pl";

################################################################
open ( STDERR, ">>$base_dir/Log" ) or die "$!";
my $now_string = localtime;


######STATE - variables##########################################
#determine the query state by retrieving CGI variables
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
my $input_cutoff=$query->param('cutoff');
my $input_model_1_name=$query->param('model_1_name')||undef;
my $input_model_2_name=$query->param('model_2_name')||undef;
my $input_filehandle=$query->upload('file')||undef;
my $input_identifier=$query->param('identifier')||undef;
my $input_select_slice=$query->param('select_slice')||undef;
my $input_select_slice_filter=$query->param('select_slice_filter')||undef;
my $checked_input_present;
my $provided_input="";
my @input_error;
my $error_message="";
my $specify_selection_error_message;
my $tempdir;
my $result_number;
my $filtered_number;
my $cutoff;
my $model_1_name;
my $model_2_name;
my $identifier;

unless(-e "$upload_dir/RF00005.cm"){
    print STDERR "CMCws: Covarinance model for demo mode 1 is missing, copy it from data/Rfam11/ to html/upload";
}
unless(-e "$upload_dir/mode2.cm"){
    print STDERR "CMCws: Covarinance model for demo mode 2 is missing. It consists of RF00005 RF00023 RF01849 RF01850 RF01851 RF01852 copy it from data/ to html/upload";
}
#TODO -add check for presence of stockholm sample files

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
    if($uploaded_file eq "sample_mode_1"){
	#set to tRNA model 
	$uploaded_file="RF00005.cm"
    }elsif($uploaded_file eq "sample_mode_2"){	
	$uploaded_file="mode2.cm"
    }elsif(-e "$upload_dir/$uploaded_file"){
	#file exists
    }elsif(-e "$rnalien_tmp_dir/$uploaded_file/result.cm"){
        #file exists
    }else{
	print STDERR "cmcws: nonexistent uploaded file has been supplied as parameter\n";
	$uploaded_file="";
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
    if(-e "$base_dir/$tempdir/result$input_result_number"){
	$result_number=$input_result_number;    
    }else{
	print STDERR "cmcws: nonexistent result_number has been supplied as parameter\n";
    }
}

#input_model_1_name
if(defined($input_model_1_name)){
    if($input_model_1_name=~/\w+/){
	$model_1_name=$input_model_1_name;    
    }else{
	#todo : return rfam error message
	$model_1_name="none";
	print STDERR "cmcws: model_1_name_invalid\n";
    }
}else{
    $model_1_name="none";
}

#input_model_2_name
if(defined($input_model_2_name)){
    if($input_model_2_name=~/\w+/){
	$model_2_name=$input_model_2_name;    
    }else{
	$model_2_name="none";
	#todo : return rfam error message
	print STDERR "cmcws: model_2_name_invalid\n";
    }
}else{
    $model_2_name="none";
}

#input-file
if(defined($input_filename)){
    #print STDERR "cmcws: Found upload /n";
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
    my $max_filesize =1500000;
    #first level
    if($check_size < 1){
	print STDERR "Uploaded Input file is empty\n";
	push(@input_error,"Uploaded Input file is empty");
    }elsif($check_size > $max_filesize){
	print STDERR "Uploaded Input file is too large\n";
	push(@input_error,"Uploaded Input file is too large");
    }else{
	#2nd level
	print STDERR "2nd level\n";
	my $check_array_reference=&check_input($name);
	my @check_array = @$check_array_reference;
	my $number_of_models=((@check_array-1)/2);
	print STDERR "Number of models: $number_of_models\n";
	print STDERR "check-array: @check_array\n";
	
	if($number_of_models>10){
	    print STDERR "Please provide 10 models or less\n";
	    push(@input_error,"Please provide 10 models or less");
	}elsif(($number_of_models==1)&&($mode==2)){
	    print STDERR "Please provide at least 2 models\n";
	    push(@input_error,"Please provide at least 2 models");
	}else{
	    #print STDERR "Array checked: @check_array\n";
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
		$number_of_models=((@check_array)/2)-1;
		my $counter=0;
		$provided_input.="<br>";
		if($number_of_models>5){
		    $provided_input.="$number_of_models models"
		}else{
		    for(0..$number_of_models){
			$counter++;
		    #todo: continue here - each line should contain number, type of input, name (if present)
			my $type=shift(@check_array);
			my $name=shift(@check_array);
			$provided_input=$provided_input."$counter. $type"." $name<br>";
		}
	    }
		$provided_input.="<br>";
	    }
	}
    }
    
}else{
   #Submit without file, set error message and request file
   unless(defined($uploaded_file)){
   	push(@input_error,"No input file provided");
   }
}
#filtered_number
if(defined($input_filtered_number)){
    if($input_filtered_number =~ /^\d+/){
	#only numbers = Taxid - preset on form in taxid field
	$filtered_number = $input_filtered_number;
    }#todo:else
}else{
    $filtered_number=10;
}
#identifier
#todo -fix identifier taintcheck
#if(defined($input_identifier)){
#    if($input_identifier =~ /^\d+\_\d+/){
#	#only numbers = Taxid - preset on form in taxid field
#	$identifier = $input_identifier;
#    }#todo:else
#}else{
#    $input_identifier=undef;
#}
$identifier= $input_identifier;

#print STDERR "$mode $page\n";

#cutoff
if(defined($input_cutoff)){
    if($input_cutoff =~ /^[0-9]+$/){
	$cutoff = $input_cutoff;
    }elsif($input_cutoff=~/^-[0-9]+$/){
	$cutoff = $input_cutoff;
    }elsif($input_cutoff=~/^[0-9]+.[0-9]+$/){
	$cutoff = $input_cutoff;
    }elsif($input_cutoff=~/^-[0-9]+.[0-9]+$/){
	$cutoff = $input_cutoff;
    }else{
	$cutoff="none";
    }
#}elsif($input_cutoff eq ""){
#    $cutoff="none";
}else{
    $cutoff="none";
}

#get ids of values to be compared vs each other in mode 2 from mode 1 result list
my @postprocess_selected;
my $postprocess_value;
foreach my $name(@names){
    if($name =~ m/^p[0-9]+/){
	#check value
	$postprocess_value = $query->param("$name");
	#print STDERR "Postprocess $postprocess_value\n";
	if (($postprocess_value =~/\w+/)&&(length($postprocess_value)<250)){
	    push(@postprocess_selected, $postprocess_value);
	    print STDERR "Postprocess $postprocess_value\n";
	}
    }
}

#sets the slice of rfam to compare against
# if the slice is specified manually and wrong we return to the submit page
my @models;
my $select_slice;
my @specify_selection_error;
if($page==0){  
    $select_slice=undef;
}elsif(defined($input_select_slice)){
    my $Rfam_types="All antisense CRISPR Intron miRNA rRNA splicing antitoxin frameshift_element IRES overview scaRNA sRNA CD-box Gene leader riboswitch snoRNA thermoregulator Cis-reg HACA-box lncRNA ribozyme snRNA tRNA";
    $input_select_slice=~s/\s//;
    if($Rfam_types=~/$input_select_slice/){
	print STDERR "CMCWS - cmcws.cgi - $input_select_slice seems valid\n";
	$select_slice=$input_select_slice;
    }elsif($input_select_slice=~/specify-selection/){
	#the user has specified a filter for comparison models
	#check if it is valid
	print STDERR "Detected filter specification\n";
	if(defined($input_select_slice_filter)){
	    #should only contain RF-,[0-9] symbols
	    print STDERR "Filter specification: $input_select_slice_filter\n";
	    my $forbidden_characters = $input_select_slice_filter;
	    $forbidden_characters =~ s/R|F|-|,|[0-9]+//g;
	    if($forbidden_characters ne ""){ 
		#string contains unwanted characters - return error #TODO check if unwanted charakters filter works
		push(@specify_selection_error,"Filter contains forbidden characters $forbidden_characters");
		print STDERR "Filter contains forbidden characters $forbidden_characters\n";
	    }else{
		#only allowed characters - parse filter
		print STDERR "Filter specification only allowed characters - parsing filter specification\n";
		if($input_select_slice_filter=~/,/){
		    #we have several models or ranges
		    print STDERR "Filter specification multiple models or ranges detected\n";
		    #single models are just added to the models array, ranges are transformed into model lists and also added to the model list
		    my @ranges = split (/,/,$input_select_slice_filter);
		    foreach my $range (@ranges){
			if($range=~/-/){
			    #range of models - should contain only two delimiters
			    my @delimiters=split (/-/,$range);
			    if(@delimiters!=2){
				#bigger than expected
				push(@specify_selection_error,"Provide exactly 2 models in a range");
				print STDERR "Provide exactly 2 models in a range\n";
			    }else{		    
				#check if delimiter 1 exists
				my $model1_exists=Rfam_model_exists($delimiters[0]);
				#check if delimiter 2 exists
				my $model2_exists=Rfam_model_exists($delimiters[1]);
				#get range of models between
				my $range_models_array_reference=get_Rfam_model_range($delimiters[0],$delimiters[1]);
				my @range_models_array=@$range_models_array_reference;
				#add to @models
				@models=(@models,@range_models_array);
			    }
			}else{
			    #single model
			    #check if model exits
			    my $model1_exists=Rfam_model_exists($range);
			    if($model1_exists){
				#add to @models
				push(@models,"$range");
			    }else{
				push(@specify_selection_error,"The specified model $range does not exist");
				print STDERR "The specified model $range does not exist\n";
			    }
			}
		    }
		}else{
		    #filter contains no , that means we have a range or a single model
		    print STDERR "Filter specification single model or range detected\n";
		    if($input_select_slice_filter=~/-/){
			#range of models - should contain only two delimiters
			my @delimiters=split (/-/,$input_select_slice_filter);
			if(@delimiters!=2){
			    #bigger than expected
			    push(@specify_selection_error,"Provide exactly 2 models in a range");
			    print STDERR "Provide exactly 2 models in a range\n";
			}else{		    
			    #check if delimiter 1 exists
			    my $model1_exists=Rfam_model_exists($delimiters[0]);
			    #check if delimiter 2 exists
			    my $model2_exists=Rfam_model_exists($delimiters[1]);
			    #get range of models between
			    my $range_models_array_reference=get_Rfam_model_range($delimiters[0],$delimiters[1]);
			    my @range_models_array=@$range_models_array_reference;
			    #add to @models
			    @models=(@models,@range_models_array);
			}
		    }else{
			#single model
			my $model1_exists=Rfam_model_exists($input_select_slice_filter);
			if($model1_exists){
			    #add to @models
			    push(@models,"$input_select_slice_filter");
			}else{
			    push(@specify_selection_error,"The specified model $input_select_slice_filter does not exist");
			    print STDERR "The specified model $input_select_slice_filter does not exist\n";
			}
		    }
		}
	    }
	}	
    }else{
	#return error that filter has to be specified
	push(@specify_selection_error,"Please specify a filter");
    } 
}elsif($mode==2){
    $select_slice="All";
}elsif(-e "$base_dir/$tempdir/slice"){
    #read slice from file
    open (SLICE, "<$base_dir/$tempdir/slice") or die "Could not open slice-file: $!\n";
    $select_slice=<SLICE>;
    close SLICE;
}else{
    $select_slice="All";
}


#upon submission of a wrongly defined slice we return users to the submit page with an error message
if(@specify_selection_error && $input_select_slice=~/specify-selection/){
    # There is a problem with the slice specification
    $page=0;
    #empty input error, it is already checked.
    @input_error=undef;
    print STDERR "specify selection error: @specify_selection_error\n";
    $checked_input_present=1;
}elsif($input_select_slice_filter){
    print STDERR "No specify selection error\n";  
    print STDERR "Models in filter @models\n";
    #remove multiple models
    @models=uniq @models;
    $select_slice="specify-selection";
}

###########################################

unless($page==1){
    print STDERR "Query - $now_string - Page $page Mode $mode\n";
}


################ INPUT #####################################
    
if($page==0){
    #print $query->header();
    print "Content-type: text/html; charset=utf-8\n\n";
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ["$source_dir/template"],
	RELATIVE=>1
				 });
    my $file = "input.html";
    my $input_script_file="inputscriptfile";
    my $disabled_upload_form="";
    my $submit_form="";
    $specify_selection_error_message="";
    #Three different states of the input page
    if($checked_input_present){
	$file = "input2.html";
	if($mode eq "1"){
	    #comparison of one model vs rfam 
	    $input_script_file = "inputstep2scriptfile";
	    $disabled_upload_form="inputstep2mode1disable";
	    $submit_form="inputstep2mode1submit";
	    $specify_selection_error_message=join('/n',@specify_selection_error);
	    #print STDERR "Reached Page=0 step=2 mode=1\n";
	}elsif($mode eq "2"){
	    #comparison of multiple models with each other 
	    $input_script_file = "inputstep2scriptfile";
	    $disabled_upload_form="inputstep2mode2disable";
	    $submit_form="inputstep2mode2submit";
	    $specify_selection_error_message="";
	    #print STDERR "Reached Page=0 step=2 mode=2\n";
	}
    }elsif($mode=="0"){
	#print STDERR "Reached Page=0 step=1 mode=0\n";
    }else{
	#Input error
	$input_script_file = "inputerrorscriptfile";
	$error_message=join('/n',@input_error);
	#print STDERR "Reached Page=0 step=1 mode=$mode\n";
	print STDERR "Error: @input_error\n";
	$specify_selection_error_message="";
    }
    
    my $vars = {
	#define global variables for javascript defining the current host (e.g. linse) for redirection
	serveraddress => "$server",
        staticcontentaddress => "$server_static",
	title => "CMcompare - Webserver - Input form",
	banner => "$server_static/pictures/banner.png",
	scriptfile => "$input_script_file",
	stylefile => "inputstylefile",
	mode => "$mode",
	error_message => "$error_message",
	specify_selection_error_message => "$specify_selection_error_message",
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
	INCLUDE_PATH => ["$source_dir/template"],
	RELATIVE=>1
				 });
    my $file = "processing.html";
    my $processing_script_file="processingscriptfile";
    my $error_message="";
    my $query_number="";
    my %Rfam_types_occurence;
    my $progress_redirect;
    open (RFAMTYPES, "<$source_dir/data/types/overview")or die "Could not open : $!\n";
    while (<RFAMTYPES>){
	chomp;
	my ($key,$value) = split /;/;
	$Rfam_types_occurence{$key}=$value;
	#print STDERR "CMCws - cmcws.cgi: Rfamtype-hash: $key : $Rfam_types_occurence{$key}\n";
    }
    close RFAMTYPES;
    my $number_of_rfam_models;
    unless($select_slice eq "specify-selection"){
	$number_of_rfam_models = $Rfam_types_occurence{$select_slice};
    }elsif(defined($tempdir)){
	if(-e "$base_dir/$tempdir/slice_models"){
	    open (SLICEMODELS, "<$base_dir/$tempdir/slice_models") or die "Could not open slice-file_models: $!\n";
	    my $slice_model_string=<SLICEMODELS>;
	    my @slice_models=split(/\n/,$slice_model_string);
	    $number_of_rfam_models=@slice_models;
	    close (SLICEMODELS);
	}else{
	    print STDERR "No slice-selection model file present\n";
	}
    }else{
	$number_of_rfam_models=@models;
    }
    #print STDERR "CMCws - cmcws.cgi: Select_slice: $select_slice\n";
    #print STDERR "number of Rfam-Models: $number_of_rfam_models\n";
    my $processing_table_content="";
    #Check mode
    #Prepare the input by creating a file for each model
    unless(defined($tempdir)){
	$tempdir = tempdir ( DIR => $base_dir );
	$tempdir =~ s/$base_dir\///;
	chmod 0755, "$base_dir/$tempdir";
	#write slice file
	open (SLICE, ">$base_dir/$tempdir/slice") or die "Could not open slice-file: $!\n";
	print SLICE "$select_slice";
	close SLICE;
	if(@models){
	    open (SLICEMODELS, ">$base_dir/$tempdir/slice_models") or die "Could not open slice-file_models: $!\n";
	    my $model_string=join('\n',@models);
	    print SLICEMODELS "$model_string";
	    close SLICEMODELS;
	}
    }
    my $query_number_file_present;
    if(-e "$base_dir/$tempdir/query_number"){
	$query_number_file_present=1;
    }else{
	$query_number_file_present=0;
    }
    #print STDERR "query_number_file_present $query_number_file_present\n";
    my $postprocess_selected_check=@postprocess_selected;
    #print STDERR "postprocess_selected_check $postprocess_selected_check\n";
    if(($query_number_file_present) && (!($postprocess_selected_check))){
	open (QUERYNUMBERFILE, "<$base_dir/$tempdir/query_number")or die "Could not open $tempdir/query_number: $!\n";
	$query_number=<QUERYNUMBERFILE>;
	close QUERYNUMBERFILE;
	if($mode eq "1"){
	    #each submitted model is compared against rfam
	    #assemble output
	    my $counter=1;
	    for(1..$query_number){
		my $query_id=$counter;
		my $queueing_status="";
		my $model_comparison="";
		my $parsing_output="";
		my $result_page_link="";
		if(-e "$base_dir/$tempdir/done$counter"){$queueing_status="Done";}
		elsif(-e "$base_dir/$tempdir/begin$counter") {$queueing_status="Processing..";}
		else{$queueing_status="Queued";}
		if(-e "$base_dir/$tempdir/result$counter"){
		    my $result_lines=`cat $base_dir/$tempdir/result$counter | wc -l`;
		    my $progress_percentage=($result_lines/($number_of_rfam_models))*100;
		    my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage);
		    $model_comparison="Progress: $rounded_progress_percentage%";}
		else {$model_comparison="";}
		if(-e "$base_dir/$tempdir/done$counter"){$parsing_output="done";}
		elsif(-e "$base_dir/$tempdir/filtered_table$counter"){$parsing_output="processing..";}
		else {$parsing_output="";}
		if(-e "$base_dir/$tempdir/done$counter"){
		    $result_page_link="<a href=\"$server/cmcws.cgi?page=2&mode=$mode&tempdir=$tempdir&result_number=$counter\">Link</a>"; 
		    if($query_number==1){
			$progress_redirect="<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=2&mode=$mode&tempdir=$tempdir&result_number=$counter\"\', 5000);    
          </script>";
		    }
		}else{$result_page_link=""}
		
		$processing_table_content=$processing_table_content."<tr><td>$query_id</td><td>$queueing_status</td><td>$model_comparison</td><td>$parsing_output</td><td>$result_page_link</td></tr>";
		$counter++;
	    }
	}elsif($mode eq "2"){	
	    #the models are compared againsted each other
	    #the progress counter must consider postprocessing .. then query number is an invalid measure   
	    my $counter=1;
	    my $query_id=1;
	    my $queueing_status="";
	    my $model_comparison="";
	    my $parsing_output="";
	    my $result_page_link="";
	    #to fill the necessary fields of the result matrix we need (query_number)*(query_number)-query_number comparisons
	    my $number_of_comparisons=(($query_number*$query_number)-$query_number)/2;
	    if(-e "$base_dir/$tempdir/done$counter"){$queueing_status="Done";}
	    elsif(-e "$base_dir/$tempdir/begin$counter") {$queueing_status="Processing..";}
	    else{$queueing_status="Queued";}
	    if(-e "$base_dir/$tempdir/result$counter"){
		my $result_lines=`cat $base_dir/$tempdir/result$counter | wc -l`;
		my $progress_percentage=($result_lines/($number_of_comparisons))*100;
		my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage);
		$model_comparison="Progress: $rounded_progress_percentage%";}
		else {$model_comparison="";}
	    if(-e "$base_dir/$tempdir/done$counter"){$parsing_output="done";}
	    elsif(-e "$base_dir/$tempdir/filtered_table$counter"){$parsing_output="processing..";}
	    else {$parsing_output="";}
	    if(-e "$base_dir/$tempdir/done$counter"){
		$result_page_link="<a href=\"$server/cmcws.cgi?page=2&mode=$mode&tempdir=$tempdir&result_number=$counter\">Link</a>"; 
		$progress_redirect="<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=2&mode=$mode&tempdir=$tempdir&result_number=$counter\"\', 5000);    
          </script>";
	    }else{$result_page_link=""}
	    $processing_table_content=$processing_table_content."<tr><td>$query_id</td><td>$queueing_status</td><td>$model_comparison</td><td>$parsing_output</td><td>$result_page_link</td></tr>";	    
	    
	}
    }else{
	$processing_table_content=$processing_table_content."<tr><td>Loading</td></tr>";
    }
    
    my $covariance_dir_present;
    if(-e "$base_dir/$tempdir/covariance_model"){
	$covariance_dir_present=1;
    }else{
	$covariance_dir_present=0;
    }
    unless($covariance_dir_present){
	#if @postprocess_selected is filled we get the results for the comparison between input
	#and rfam models from the array.

	#add to path or taintcheck will complain
	$ENV{PATH}="$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
	mkdir("$base_dir/$tempdir/covariance_model",0744);
	mkdir("$base_dir/$tempdir/stockholm_alignment",0744);
	open (COMMANDS, ">$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";	
	print COMMANDS "#!/bin/bash\n";
        #Include case of passing result file from RNAlien
        if(-e "$rnalien_tmp_dir/$uploaded_file/result.cm"){
		print COMMANDS "cp $rnalien_tmp_dir/$uploaded_file/result.cm $base_dir/$tempdir/input_file;\n";
        }else{
		print COMMANDS "cp $upload_dir/$uploaded_file $base_dir/$tempdir/input_file;\n";
        }
	print COMMANDS "cd $base_dir/$tempdir/;\n";
	print COMMANDS "$source_dir/executables/split_input.pl $base_dir/$tempdir/input_file $base_dir/$tempdir/;\n";
	print COMMANDS "$source_dir/executables/convert_stockholmdir_to_cmdir.pl $base_dir/$tempdir $source_dir;\n";
	print COMMANDS "$source_dir/executables/calculate.pl $server $server_static $tempdir $source_dir $mode $select_slice;\n";
	
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
            #print STDERR "export SGE_ROOT=$sge_root_directory; $qsub_location -N IP$ip_adress -q web_short_q -e $base_dir/$tempdir/error -o $base_dir/$tempdir/error $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid";
	    #exec "export SGE_ROOT=$sge_root_directory; $qsub_location -N IP$ip_adress -q web_short_q -e $base_dir/$tempdir/error -o $base_dir/$tempdir/error $base_dir/$tempdir/commands.sh > $base_dir/$tempdir/Jobid" or die "Could not execute sge submit: $! /n";
	    print STDERR "$qsub_location -N IP$ip_adress -q $sge_queue_name -e $base_dir/$tempdir/error -o $base_dir/$tempdir/error $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid";
            exec "$qsub_location -N IP$ip_adress -q $sge_queue_name -e $base_dir/$tempdir/error -o $base_dir/$tempdir/error $base_dir/$tempdir/commands.sh > $base_dir/$tempdir/Jobid" or die "Could not execute sge submit: $! /n";
	}
    }elsif(@postprocess_selected){
	#print STDERR "Got here right\n";
	#create new tempdir
	my $oldtempdir=$tempdir;	    
	$tempdir = tempdir ( DIR => $base_dir );
	$tempdir =~ s/$base_dir\///;
	chmod 0755, "$base_dir/$tempdir";
	#add to path or taintcheck will complain
	$ENV{PATH}="$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
	mkdir("$base_dir/$tempdir/covariance_model",0744);
	mkdir("$base_dir/$tempdir/stockholm_alignment",0744);
	open (COMMANDS, ">$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";	
	print COMMANDS "#!/bin/bash\n";
	#copy the models of choice there and continue with normal mode 2 procedure
	my $postprocess_counter=1;
	my $rfam_model_dir="$source_dir"."/data/Rfam11";
	foreach my $postprocess_file (@postprocess_selected){
	    if($postprocess_counter==1){
		copy("$base_dir/$oldtempdir/covariance_model/$postprocess_file","$base_dir/$tempdir/covariance_model/$postprocess_file") or die "Copy failed: $!";
	    }else{
		#print STDERR "Copy: $rfam_model_dir/$postprocess_file $base_dir/$tempdir/covariance_model/$postprocess_file\n";
		copy("$rfam_model_dir/$postprocess_file.cm","$base_dir/$tempdir/covariance_model/input$postprocess_counter.cm") or die "Copy failed: $!";
		}
	    $postprocess_counter++;
	}
	$postprocess_counter=$postprocess_counter-1;
	#in the postprocessing case querynumber is created here, this is normally done by split input
	open (QUERYNUMBER, ">$base_dir/$tempdir/query_number") or die "Could not create query_number";
	print QUERYNUMBER "$postprocess_counter";
	close QUERYNUMBER;
	print COMMANDS "$source_dir/executables/calculate.pl $server $server_static $tempdir $source_dir $mode $select_slice;\n";
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
	    exec "export SGE_ROOT=$sge_root_directory; $qsub_location -N IP$ip_adress -q $sge_queue_name -e /$base_dir/$tempdir/error -o /$base_dir/$tempdir/error $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid" or die "Could not execute sge submit: $! /n";
	}
    }
    
    unless(defined($progress_redirect)){
	$progress_redirect="<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);    
          </script>";
    }
    my $link="$server/cmcws.cgi?"."page=1"."&tempdir=$tempdir"."&mode=$mode";
    my $vars = {
	#define global variables for javascript defining the current host (e.g. linse) for redirection
	serveraddress => "$server",
	staticcontentaddress => "$server_static",
	title => "CMcompare - Webserver - Processing",
	banner => "$server_static/pictures/banner.png",
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
	INCLUDE_PATH => ["$source_dir"],
	RELATIVE=>1
				 });
    my $output_script_file="template/outputscriptfile";
    my $total;
    if($mode eq "1"){
	unless(-e "$base_dir/$tempdir/slice_models"){
	    my %Rfam_types_occurence;
	    #TODO add support for filter_slice
	    open (RFAMTYPES, "<$source_dir/data/types/overview") or die "Could not open : $!\n";
	    while (<RFAMTYPES>){
		chomp;
		my ($key, $value) = split /;/;
		$Rfam_types_occurence{$key}=$value;
	    }
	    close RFAMTYPES;
	    $total=$Rfam_types_occurence{$select_slice};
	}else{
	    #slices are specified
	    open (SLICEMODELS, "<$base_dir/$tempdir/slice_models") or die "Could not open slice-file_models: $!\n";
	    my $slice_model_string=<SLICEMODELS>;
	    my @slice_models=split(/,/,$slice_model_string);
	    $total=@slice_models;
	    close (SLICEMODELS);
	}
    }else{
	open (QUERYNUMBERFILE, "<$base_dir/$tempdir/query_number") or die "Could not open $tempdir/query_number: $!\n";
	my $query_number=<QUERYNUMBERFILE>;
	close QUERYNUMBERFILE;
	#number of comparisons
	$total=(($query_number*$query_number)-$query_number)/2;
    }
    my $error_message="";
    my $vars;
    my $file;
    my $inputid;
    my $inputname;
    #get input id and name
    if(-e "$base_dir/$tempdir/inputidname$result_number"){
	open (INPUTIDNAME, "<$base_dir/$tempdir/inputidname$result_number")or die "Could not open $base_dir/$tempdir/inputidname$result_number: $!\n";
	my $input_id_name_string=<INPUTIDNAME>;
	close INPUTIDNAME;
	my @input_id_name_array=split(/;/,$input_id_name_string);
	$inputid=$input_id_name_array[0];
	$inputname=$input_id_name_array[1];
    }else{
	#print STDERR "cmcws: Error inputidname$result_number does not exist in tempdir $base_dir/$tempdir";
    }
    `$source_dir/executables/output_to_html.pl $server $server_static $base_dir $tempdir $result_number $mode $filtered_number $cutoff $model_1_name $model_2_name`==0 or die print STDERR "cmcws: could not execute\n";
    #close STDERR;
    #number_of_hits_to_display_after_applying_filters read back in from file written by output_to_html.pl
    open (NUMBEROFHITS, "<$base_dir/$tempdir/number_of_hits$result_number")or die "Could not open $tempdir/number_of_hits$result_number: $!\n";
    my $number_of_hits_to_display=<NUMBEROFHITS>;
    close NUMBEROFHITS;   
    #Check mode
    if($mode eq "1"){
	if(-e "$base_dir/$tempdir/done$result_number"){	
	    #each submitted model is compared against rfam
	    $file = 'template/output.html';
	    $output_script_file="template/outputscriptfile";
	    $vars = {
		#define global variables for javascript defining the current host (e.g. linse) for redirection
		serveraddress => "$server",
		staticcontentaddress => "$server_static",
		title => "CMcompare - Webserver - Output - Comparison vs Rfam",
		banner => "$server_static/pictures/banner.png",
		scriptfile => "$output_script_file",
		stylefile => "template/outputstylefile",
		mode => "$mode",
		filter_fields =>"template/output_filter_fields1",
		table_header => "template/output_table_header1",
		output_title =>"Top $number_of_hits_to_display pairwise comparisons of $total total for $inputid - $inputname<br><h4>Current cutoffs (Max. hits: $filtered_number , Min. Link score: $cutoff , Rfam name containing: $model_1_name)</h4>",
		inputid => "$inputid",
		filtered_table => "html/$tempdir/filtered_table$result_number",
		cm_map => "$server_static/tmp/$tempdir/graph"."$result_number".".svg",
		cm_output_file => "$server_static/tmp/$tempdir/result$result_number",
		csv_file => "$server_static/tmp/$tempdir/csv$result_number",
		csv_filtered_file => "$server_static/tmp/$tempdir/csv_filtered$result_number",
		dot_file => "$server_static/tmp/$tempdir/graph_out$result_number.dot",
		svg_file => "$server_static/tmp/$tempdir/graph"."$result_number".".svg",
		result_list_form_and_table => "template/output_result_list_form_table1",
		result_matrix =>"template/output_result_matrix1",
		result_number =>"$result_number",
		tempdir => "$tempdir",
		error_message => "$error_message"
	    };
	    #print STDERR "cmcws: Page:2 Mode:1 reached/n";
	}else{
	    print "<script>
	     window.setTimeout (\'window.location = \"$server/cmcws.cgi?page=1&mode=$mode&tempdir=$tempdir\"\', 5000);    
          </script>\n";
	    #todo add errormessage that results are not yet available
	}
    }elsif($mode eq "2"){
	#the models are compared againsted each other and optionally additionally against rfam
	#display the overview page
	if(-e "$base_dir/$tempdir/done$result_number"){	
	    #each submitted model is compared against rfam
	    $file = 'template/output.html';
	    $output_script_file="template/outputscriptfile";
	    $vars = {
		#define global variables for javascript defining the current host (e.g. linse) for redirection
		serveraddress => "$server",
		staticcontentaddress => "$server_static",
		title => "CMcompare - Webserver - Output - Comparison of a model set",
		banner => "$server_static/pictures/banner.png",
		scriptfile => "$output_script_file",
		stylefile => "template/outputstylefile",
		mode => "$mode",
		output_title=> "Top $number_of_hits_to_display pairwise comparisons of total $total <br><h4>Current cutoffs (Max. hits: $filtered_number , Min. Link score: $cutoff , Model Name 1 containing: $model_1_name , Model Name 2 containing: $model_1_name)</h4>",
		filter_fields=>"template/output_filter_fields2",
		table_header=> "template/output_table_header2",
		filtered_table => "html/$tempdir/filtered_table$result_number",
		cm_map=> "$server_static/tmp/$tempdir/graph$result_number.svg",
		cm_output_file => "$server_static/tmp/$tempdir/result$result_number",
		csv_file => "$server_static/tmp/$tempdir/csv$result_number",
		csv_filtered_file => "$server_static/tmp/$tempdir/csv_filtered$result_number",
		dot_file => "$server_static/tmp/$tempdir/graph_out$result_number.dot",
		svg_file => "$server_static/tmp/$tempdir/graph$result_number.svg",
		result_list_form_and_table => "template/output_result_list_form_table2",
		result_matrix =>"html/$tempdir/result_matrix",
		result_number =>"$result_number",
		tempdir => "$tempdir",
		error_message => "$error_message"
	    };
	    #print STDERR "cmcws: Page:2 Mode:2 reached/n";
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

################ Detailed Comparison ############################

if($page==3){
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ["$source_dir/template"],
	RELATIVE=>1
				 });
    my $file = 'detailed_comparison.html';
    my $processing_script_file="processingscriptfile";
    my $error_message="";
    my $return_link;
    if($mode eq "1"){
	$return_link="$server/cmcws.cgi?"."page=2"."&tempdir=$tempdir"."&mode=$mode"."&result_number=$result_number";
    }elsif($mode eq "2"){
	$return_link="$server/cmcws.cgi?"."page=2"."&tempdir=$tempdir"."&mode=$mode"."&result_number=$result_number";
    }
    #todo: attributes missing in function call
    my $processing_table_content=&get_comparison_results("$tempdir","csv"."$result_number",$identifier);
    #gather content by reading appropiate result file --> need tempdir and result file, as well as models specified
    my $vars = {
	#define global variables for javascript defining the current host (e.g. linse) for redirection
	serveraddress => "$server",
	staticcontentaddress => "$server_static",
	title => "CMcompare - Webserver - Detailed Comparison",
	banner => "$server_static/pictures/banner.png",
	scriptfile => "$processing_script_file",
	stylefile => "inputstylefile",
	mode => "$mode",
	return_link => "$return_link",
	processing_table_content => "$processing_table_content",
	error_message => "$error_message"    
    };
    print "Content-type: text/html; charset=utf-8\n\n";
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

#############################################################

sub check_input{
    #Parameter is filename
    #File can contain multiple cm, alignments in stockholm format and HMMs
    #Begin of a stockholm-alignment is denoted by:  # STOCKHOLM 1.0
    #Begin of a cm is denoted by: INFERNAL-1 [1.0]
    #Begin of a HMM is denoted by: HMMER
    #End of a stockholm, cm, HMM entry is denoted by: //
    #We want to ignore all contained HMMs at the moment
    my $input_filename=shift;
    open (INPUTFILE, "<$upload_dir/$input_filename") or die "Cannot open input-file";
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #input_elements contains the type of input, the name and the accession number
    my @input_elements;
    #We expect a error by default and set this return value to ok if the input fits
    push(@input_elements,"error;");
    my $stockholm_alignment_detected=0;
    my $covariance_model_detected=0;
    my $hidden_markov_model_detected=0;
    my $counter=0;
    while(<INPUTFILE>){
	chomp;
	#look for header
	if(/\# STOCKHOLM/ && $stockholm_alignment_detected==0){
	    $stockholm_alignment_detected=1;
	    push(@input_elements,"Stockholm alignment -");
	    $counter++;
	}elsif(/INFERNAL/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    push(@input_elements,"Covariance model -");
	    $counter++;
	}elsif(/HMMER/ && $hidden_markov_model_detected==0){
	    $hidden_markov_model_detected=1;
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
	if(/^\/\// && ($stockholm_alignment_detected==2 || $covariance_model_detected==2 || $hidden_markov_model_detected==1)){
	    $stockholm_alignment_detected=0;
	    $covariance_model_detected=0;
	    $hidden_markov_model_detected=0;
	}
    }
    if(@input_elements>2){
	#input 
	my $input_element_count=@input_elements;
	my $unexpected_number_of_input_elements=($input_element_count-1)%2;
	#print STDERR "cmcws: Number of input element: $input_element_count, Erwartete Anzahl an Elementen gefunden: $unexpected_number_of_input_elements";
	#todo: set default name if we do not find one or this step is problematic
	if((($input_element_count-1)%2)==0){
	    #contains models
	    $input_elements[0]="true";
	}
	#print STDERR "cmcws: contains models\n";
    }else{
	#No compatible covariance models or alignments found in input
	$input_elements[0]=$input_elements[0]."No covariance models or alignments found in input<br>;";
    }   
    close INPUTFILE;
    return \@input_elements;
}

sub get_comparison_results{
    #be careful about results retrieved from the rfam result folder
    my $tempdir=shift;
    my $result_csv_file=shift;
    my $identifier=shift;
    my $attribute_table;
    my @sorted_entries;
    #csv is already present, we read it in
    open(CSVINPUT,"<$base_dir/$tempdir/$result_csv_file") or die "Can't write $base_dir/$tempdir/$result_csv_file: $!";
    while(<CSVINPUT>){
	my @entry=split(/;/,$_);
	my $entry_reference=\@entry;
	push(@sorted_entries,$entry_reference);
    }
    #get rid of the header line
    shift(@sorted_entries);
    close CSVINPUT;    
    #get requested entry
    #$attribute_table.="@sorted_entries";
    foreach(@sorted_entries){
	my @sorted_entry=@$_;
	my $link_score=$sorted_entry[0];
	my $id1=$sorted_entry[1];
	my $id1_truncated=$id1;
	$id1_truncated=~s/.cm//;
	my $id1_number=$id1_truncated;
	$id1_number=~s/input//;
	my $id2=$sorted_entry[2];
	my $id2_truncated=$id2;
	$id2_truncated=~s/.cm//;
	my $id2_number=$id2_truncated;
	$id2_number=~s/input//;
	my $current_identifier="$id1_truncated"."_"."$id2_truncated";
	if($identifier eq $current_identifier){
	    #construct attribute table
	    my $name1=$sorted_entry[3];
	    my $name2=$sorted_entry[4];
	    my $score1=$sorted_entry[5];
	    my $score2=$sorted_entry[6];
	    my $secondary_structure1=$sorted_entry[7];
	    my $secondary_structure2=$sorted_entry[8];
	    my $matching_nodes1=$sorted_entry[9];
	    my $matching_nodes2=$sorted_entry[10];
	    my $link_sequence=$sorted_entry[11];
	    #my $rounded_link_score=nearest(1, $link_score);
	    $attribute_table="<tr><td style=\"border:1px solid #000;width:2%;\">Id</td><td style=\"border:1px solid #000;\">$id1</td><td style=\"border:1px solid #000;\">$id2</td></tr>
		<tr><td style=\"border:1px solid #000;width:15%;\">Name</td><td style=\"border:1px solid #000;\">$name1</td><td style=\"border:1px solid #000;\">$name2</td></tr>
                <tr><td style=\"border:1px solid #000;width:15%;\">Score</td><td style=\"border:1px solid #000;\">$score1</td><td style=\"border:1px solid #000;\">$score2</td></tr>
                <tr><td style=\"border:1px solid #000;width:15%;\">Secondary Structure</td><td style=\"border:1px solid #000;\">$secondary_structure1</td><td style=\"border:1px solid #000;\">$secondary_structure2</td></tr>
                <tr><td style=\"border:1px solid #000;width:15%;\">Matching Nodes</td><td style=\"border:1px solid #000;\">$matching_nodes1</td><td style=\"border:1px solid #000;\">$matching_nodes2</td></tr>
                <tr><td style=\"border:1px solid #000;width:15%;\">Link score</td><td colspan=\"2\" style=\"border:1px solid #000;\" > $link_score </td></tr>
                <tr><td style=\"border:1px solid #000;width:15%;\">Link sequence</td><td colspan=\"2\" style=\"border:1px solid #000;\">$link_sequence</td></tr>";
	}
    }
    unless(defined($attribute_table)){
	$attribute_table="<tr><td></td><td colspan=\"2\">no entry found</td></tr>";
    }
    return $attribute_table;
}
close STDERR;

sub Rfam_model_exists{
    #checks if a Rfam model exists
    my $model_identifier = shift;
    my $lookup ="$source_dir/data/Rfam11/"."$model_identifier".".cm";
    if(-e $lookup){
	print STDERR "Performing model lookup - model $lookup - result 1\n";
	return "1";
    }else{
	print STDERR "Performing model lookup - model $lookup - result 0\n";
	return "0";
    }
}

sub get_Rfam_model_range{
    #returns all models that lie between
    print STDERR "processing model range\n";
    my $model_identifier1 = shift;
    my $model_identifier2 = shift;
    my @models;
    #check delimiters
    my $delimiter1_exists=&Rfam_model_exists($model_identifier1);
    my $delimiter2_exists=&Rfam_model_exists($model_identifier2);
    if($delimiter1_exists && $delimiter2_exists){
	#get numbers from id
	$model_identifier1=~/^RF(\d+)/;
	my $model_number1 = $1;
	print STDERR "model range delimiter 1: $model_identifier1 Number $model_number1\n";
	$model_identifier2=~/^RF(\d+)/;
	my $model_number2 = $1;
	print STDERR "model range delimiter 2: $model_identifier2 Number $model_number2\n";
	$model_number1=~s/^0+//;
	$model_number2=~s/^0+//;
	print STDERR "model range numbers wo leading zeros: $model_number1 $model_number2\n";
	my $lower_boundry= min($model_number1,$model_number2);
	my $upper_boundry= max($model_number1,$model_number2);
	my $counter=$lower_boundry;
	for($lower_boundry..$upper_boundry){
	    my $current_id_number = sprintf("%05d", $counter);
	    my $current_id="RF"."$current_id_number";
	    my $current_id_exists=&Rfam_model_exists($current_id);
	    if($current_id_exists){
		push(@models,$current_id);
	    }
	    $counter++;
	}
    }else{
	#one of our delimiters does not exist
	push(@models,"Error: one of our delimiters does not exist");
    }
    return \@models;
}
