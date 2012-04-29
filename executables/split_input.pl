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
    while(<INPUTFILE>){
	#look for header
	if(/\# STOCKHOLM 1\./ && $stockholm_alignment_detected==0){
	    $stockholm_alignment_detected=1;
	    $counter++;
	    push(@model,$_);
	}elsif(/INFERNAL\-1 \[1/ && $covariance_model_detected==0){
	    $covariance_model_detected=1;
	    $counter++;
	    push(@model,$_);
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
	}
       #todo: error if we detected a header or a name but no end (//)
    }
    close INPUTFILE;
    open (QUERYNUMBERFILE, ">$input_tempdir"."query_number")or die "Could not create query number:$input_tempdir/query_number: $!\n";
    print QUERYNUMBERFILE "$counter";
    close QUERYNUMBERFILE;
}    
    #if(@input_elements>2){
    #input 
#	my $input_element_count=@input_elements;
#	my $unexpected_number_of_input_elements=($input_element_count-1)%2;
#	print STDERR "cmcws: Number of input element: $input_element_count, Erwartete Anzahl an Elementen gefunden: $unexpected_number_of_input_elements";
#	if((($input_element_count-1)%2)==0){
#	    #contains models
#	    $input_elements[0]="true";
#	}
#	print STDERR "cmcws: contains models\n";
    #   }else{
#	#No covariance models or alignments found in input
#	$input_elements[0]=$input_elements[0]."No covariance models or alignments found in input<br>;";
#    }   
#    close INPUTFILE;
#    return \@input_elements;


#sub prepare_input{
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
#}

