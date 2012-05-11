#!/usr/bin/perl 
#Splits files containing 1 or more covariance models and/or stockholm alignments into one file per model/alignment  
use warnings;
use strict;
use diagnostics;

print STDERR "cmcws: launched calculate.pl\n";

#Input is path to file that should be split
my $tempdir_input=$ARGV[0];
my $input_source_dir=$ARGV[1];
my $mode_input=$ARGV[2];
my $tempdir;
my $mode;
my $source_dir;
#tempdir

if(defined($input_source_dir)){
    if(-e "$input_source_dir"){
	$source_dir = $input_source_dir;    
    }
}else{

}

if(defined($tempdir_input)){
    if(-e "$tempdir_input"){
	$tempdir = $tempdir_input;    
    }
}else{

}

#mode
if(defined($mode_input)){
    if($mode eq "1"){
	$mode = 1;
    }elsif($mode eq "2"){
	$mode = 2;
    }
}else{
    $mode = 1;
}

#todo create progress indicators
if(defined($tempdir)){
    my $alignment_dir="$tempdir/stockholm_alignment";
    my $model_dir="$tempdir/covariance_model";
    my $executable_dir="$source_dir"."/executables";
    my $rfam_model_dir="$source_dir"."/data/Rfam10.1";
    my $file;
    my $rfam_file;
    chdir($tempdir);
    opendir(DIR, $model_dir) or die "can't opendir $model_dir: $!";
    my $counter=1;
    while (defined($file = readdir(DIR))) {
	unless($file=~/^\./){
	    #compute
	    opendir(RFAMDIR, $rfam_model_dir) or die "can't opendir rfam dir - $rfam_model_dir: $!";
	    open(BEGIN,">$tempdir/begin$counter") or die "Can't create begin$counter: $!";
	    close(BEGIN);	    
	    while (defined($rfam_file = readdir(RFAMDIR))) {
		unless($rfam_file=~/^\./){  
		    #print STDERR "cmcws: exec file $file, rfam-file $rfam_file\n";
		    #print "$executable_dir/CMCompare $model_dir/$file $rfam_model_dir/$rfam_file >>$tempdir/result$counter\n";
		    system("$executable_dir/CMCompare $model_dir/$file $rfam_model_dir/$rfam_file \>\>$tempdir/result$counter")==0 or die "cmcws: Execution failed:  File $file - $!";
		}
	    }
	    open(DONE,">$tempdir/done$counter") or die "Can't create $tempdir/done$file: $!";
	    close(DONE);
	    #compute output 
	    system("$executable_dir/output_to_html.pl $tempdir $mode $counter 20")==0 or die "cmcws: Execution failed: File $file - $!";
	    $counter++;
	}
    }
    closedir(DIR);	
    closedir(RFAMDIR);
}
