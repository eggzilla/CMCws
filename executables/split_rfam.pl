#!/usr/bin/perl 
#Splits files containing 1 or more covariance models and names them according to rfam id  
# executables/split_rfam.pl /srv/http/cmcws_data/Rfam.cm.1_1 /srv/http/cmcws_data/Rfam11/
#./split_rfam.pl Rfam.cm.1_1 /scratch/egg/projects/cm_compare_webserver/Rfam_matrix/
use warnings;
use strict;
use diagnostics;

#Input is path to file that should be split
my $filename_input=$ARGV[0];
my $tempdir_input=$ARGV[1];
my $filename="";
my $tempdir="";
#tempdir
if(defined($tempdir_input)){
    if(-e "$tempdir_input"){
	$tempdir = $tempdir_input;    
        }
}else{
    $tempdir = "";
}

#filename
if(defined($filename_input)){
    if(-e "$filename_input"){
	#file exists
	$filename="$filename_input";
        }
}else{
    $filename = "";
}

#print  "cmcws: called split_input with arg1:$filename, arg2:$tempdir\n";
#create a new subfolder for the splits in the tempdir
print "Calling splitinput\n";
split_input($filename,$tempdir);
#Array with split
sub split_input{
    #Parameter is filename
    #File can contain multiple cm or alignments in stockholm format
    #Begin of a stockholm-alignment is denoted by:  # STOCKHOLM 1.0
    #Begin of a cm is denoted by: INFERNAL-1 [1.0]
    #End of a stockholm or cm file from rfam is denoted by: //
    my $input_filename=shift;
    my $input_tempdir=shift;
    open (INPUTFILE, "<$input_filename") or die "Cannot open $input_filename: $!\n";
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #input_elements contains the type of input, the name and the accession number
    #We expect a error by default and set this return value to ok if the input fits
    my $stockholm_alignment_detected=0;
    my $covariance_model_detected=0;
    my @model;
    #counts number of entries
    my $counter=0;
    my $Rfam_id="";
    while(<INPUTFILE>){
	#look for header
	if(/^INFERNAL/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    $counter++;
	    push(@model,$_);
	    print "Counter: $counter - Step1\n";
	}elsif($covariance_model_detected==1 || $covariance_model_detected==2){
            push(@model,$_);
        }
	
	#we look for the RFAM id
	if(/^ACC/ && $covariance_model_detected==1){
	    $covariance_model_detected=2;
	    my @split_array = split(/\s+/,$_);
	    my $last_element = @split_array - 1;
	    $Rfam_id=$split_array[$last_element];
	    print "Counter: $counter - Step2 - $Rfam_id\n";
	}
	
	#we have detected a complete entry and want to write it to file
	if(/^\/\// && $covariance_model_detected==2){
	    open (OUTPUTFILE, ">$input_tempdir"."cm/$Rfam_id.cm")or die "Could not create $input_tempdir/cm/$Rfam_id.cm: $!\n";
	    print "Counter: $counter - Step3 - writing $Rfam_id\n";
	    my $model_lines = @model-1;
	    for(0..$model_lines){
		my $line = shift(@model);
		print OUTPUTFILE "$line";
	    }
	    $covariance_model_detected=0;
	    close OUTPUTFILE;
	    $Rfam_id="";
	}
       #todo: error if we detected a header or a name but no end (//)
    }
    close INPUTFILE;
    open (QUERYNUMBERFILE, ">$input_tempdir"."query_number")or die "Could not create query number:$input_tempdir/query_number: $!\n";
    print QUERYNUMBERFILE "$counter";
    close QUERYNUMBERFILE;
}    
