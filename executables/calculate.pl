#!/usr/bin/perl 
#Splits files containing 1 or more covariance models and/or stockholm alignments into one file per model/alignment  
use warnings;
use strict;
use diagnostics;

#Input is path to file that should be split
my $filename_input=$ARGV[0];
my $tempdir_input=$ARGV[1];
my $mode_input=$ARGV[2];
my $filename;
my $tempdir;
my $mode;
#tempdir
if(defined($tempdir_input)){
    if(-e "$tempdir_input"){
	$tempdir = $tempdir_input;    
        }
}else{

}

#filename
if(defined($filename_input)){
    if(-e "$filename_input"){
	#file exists
	$filename="$filename_input";
        }
}else{
  
}
