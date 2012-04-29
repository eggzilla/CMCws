#!/usr/bin/perl 
#converts all stockholm alignment files in a subfolder called stockholm_alignment of the provided temp-dir
#into covariance_models using cmbuild from the infernal package
#and puts them in a folder called covariance_model
use warnings;
use strict;
use diagnostics;

#Input is path to file that should be split
my $input_temp_dir=$ARGV[0];
my $input_source_dir=$ARGV[1];
my $temp_dir="";
my $source_dir="";

#tempdir
if(defined($input_temp_dir)){
    if(-e "$input_temp_dir"){
	$temp_dir = $input_temp_dir;    
        }
}else{
    $temp_dir = "";
}

if(defined($input_source_dir)){
    if(-e "$input_source_dir"){
	$source_dir = $input_source_dir;    
        }
}else{
    $source_dir = "";
}

#print STDERR "Input-dir:$input_conversion_dir,untainted:$conversion_dir,Input-source-dir:$input_source_dir,untainted:$source_dir\n";

&convert_stockholm_alignment_folder($temp_dir,$source_dir);

sub convert_stockholm_alignment_folder{
    my $dir=shift;
    my $source_dir=shift;
    my $alignment_dir="$dir/stockholm_alignment";
    my $model_dir="$dir/covariance_model";
    my $executable_dir="$source_dir"."/executables";
    my $file;
    #get all filenames
    chdir($alignment_dir);
    opendir(DIR, $alignment_dir) or die "can't opendir $dir: $!";
    while (defined($file = readdir(DIR))) {
	# cmbuild my.cm trna.5.sto
	if($file=~/^\./){
	    #do nothing in case of . ..
	    print "Do nothing: $file \n";
	}else{
	    #print "$executable_dir/cmbuild $model_dir/$file $alignment_dir/$file\n";
	    exec "$executable_dir/cmbuild $model_dir/input$file.cm $alignment_dir/$file;";
	}
    }
    closedir(DIR);
    
}    
