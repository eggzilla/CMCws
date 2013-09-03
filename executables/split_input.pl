#!/usr/bin/perl 
#Splits files containing 1 or more covariance models and/or stockholm alignments into one file per model/alignment  
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
split_input($filename,$tempdir);
#Array with split
sub split_input{
    #Parameter is filename
    #File can contain multiple cm,alignments in stockholm format or hidden markov models
    #Begin of a stockholm-alignment is denoted by:  # STOCKHOLM 1.0
    #Begin of a cm is denoted by: INFERNAL-1 [1.0]
    #Begin of a hmm is denoted by: HMMER
    #End of a stockholm, cm or hmm entry is denoted by: //
    my $input_filename=shift;
    my $input_tempdir=shift;
    open (INPUTFILE, "<$input_filename") or die "Cannot open $input_filename: $!\n";
    #include taintcheck later, now we just count the number of provided alignment and cm files
    #input_elements contains the type of input, the name and the accession number
    #We expect a error by default and set this return value to ok if the input fits
    my $stockholm_alignment_detected=0;
    my $covariance_model_detected=0;
    my $hidden_markov_model_detected=0;
    my @model;
    #counts number of entries
    my $counter=0;
    while(<INPUTFILE>){
	#look for header
	if(/\# STOCKHOLM/ && $stockholm_alignment_detected==0){
	    $stockholm_alignment_detected=1;
	    $counter++;
	    push(@model,$_);
	}elsif(/INFERNAL/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    $counter++;
	    push(@model,$_);
	}elsif(/HMMER/ && $hidden_markov_model_detected==0){
	    $hidden_markov_model_detected=1;
	    #   
	}elsif($covariance_model_detected==1 || $stockholm_alignment_detected==1){
	    push(@model,$_);
	}
	#we have detected a complete entry and want to write it to file
	if(/^\/\// && $stockholm_alignment_detected==1){
	    open (OUTPUTFILE, ">$input_tempdir"."stockholm_alignment/$counter")or die "Could not create $input_tempdir/stockholm_alignment/$counter: $!\n";
	    my $model_lines = @model-1;
	    for(0..$model_lines){
		my $line = shift(@model);
		print OUTPUTFILE "$line";
	    }
	    $stockholm_alignment_detected=0;
	    close OUTPUTFILE;
	}elsif(/^\/\// && $covariance_model_detected==1){
	    open (OUTPUTFILE, ">$input_tempdir"."covariance_model/input$counter.cm")or die "Could not create $input_tempdir/covariance_model/input$counter.cm: $!\n";;
	    my $model_lines = @model-1;
	    for(0..$model_lines){
		my $line = shift(@model);
		print OUTPUTFILE "$line";
	    }
	    $covariance_model_detected=0;
	    close OUTPUTFILE;
	}elsif(/^\/\// && $hidden_markov_model_detected==1){
	    #HMM input is ignored
	    $hidden_markov_model_detected=0;
	}
       #todo: error if we detected a header or a name but no end (//)
    }
    close INPUTFILE;
    open (QUERYNUMBERFILE, ">$input_tempdir"."query_number")or die "Could not create query number:$input_tempdir/query_number: $!\n";
    print QUERYNUMBERFILE "$counter";
    close QUERYNUMBERFILE;
}    

