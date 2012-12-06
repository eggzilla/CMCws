#!/usr/bin/perl 
#Splits files containing 1 or more covariance models and/or stockholm alignments into one file per model/alignment  
use warnings;
use strict;
use diagnostics;

print STDERR "cmcws: launched calculate.pl\n";

#Input is path to file that should be split
my $server=$ARGV[0];
my $tempdir_folder=$ARGV[1];
my $input_source_dir=$ARGV[2];
my $mode_input=$ARGV[3];
my $base_dir="$input_source_dir"."/html/";
#complete path to tempdir
my $tempdir_path_input="$base_dir"."$tempdir_folder";
my $tempdir_path;
my $mode;
my $source_dir;
#tempdir

if(defined($input_source_dir)){
    if(-e "$input_source_dir"){
	$source_dir = $input_source_dir;
    }
}else{
    print STDERR "cmcws: error - calculate.ps has been called without specifing source_dir parameter";
}

if(defined($tempdir_path_input)){
    if(-e "$tempdir_path_input"){
	$tempdir_path = $tempdir_path_input;    
    }
}else{
    print STDERR "cmcws: error - calculate.pl has been called without specifing tempdir parameter";
}

#mode
if(defined($mode_input)){
    if($mode_input eq "1"){
	$mode = 1;
    }elsif($mode_input eq "2"){
	$mode = 2;
    }
}else{
    $mode = 1;
}

#todo create progress indicators
if(defined($tempdir_path)){
    my $alignment_dir="$tempdir_path/stockholm_alignment";
    my $model_dir="$tempdir_path/covariance_model";
    my $executable_dir="$source_dir"."/executables";
    my $rfam_model_dir="$source_dir"."/data/Rfam11";
    print "rfam_model_dir: $rfam_model_dir\n";
    my $file;
    my $rfam_file;
    chdir($tempdir_path);
    opendir(DIR, $model_dir) or die "can't opendir $model_dir: $!";
    my $counter=1;
    if($mode eq "1"){
	print "Calculate with mode 1\n";
	while (defined($file = readdir(DIR))) {
	    #print "While loop $file \n";
	    unless($file=~/^\./){
		#compute
		opendir(RFAMDIR, $rfam_model_dir) or die "Can't opendir rfam dir - $rfam_model_dir: $!";
		open(BEGIN,">$tempdir_path/begin$counter") or die "Can't create begin$counter: $!";
		close(BEGIN);
		#print "Written begin\n";
		while (defined($rfam_file = readdir(RFAMDIR))) {
		    unless($rfam_file=~/^\./){  
			#print "cmcws: exec file $file, rfam-file $rfam_file\n";
			#print "$executable_dir/CMCompare $model_dir/$file $rfam_model_dir/$rfam_file \>\>$tempdir_path/result$counter/n";
			system("$executable_dir/CMCompare $model_dir/$file $rfam_model_dir/$rfam_file \>\>$tempdir_path/result$counter")==0 or die "cmcws: Execution failed:  File $file - $!";
		    }
		}
		#compute output 
		system("$executable_dir/output_to_html.pl $server $base_dir $tempdir_folder $mode $counter 20")==0 or die "cmcws: Execution failed: File $file - $!";
		open(DONE,">$tempdir_path/done$counter") or die "Can't create $tempdir_path/done$file: $!";
		close(DONE);
		$counter++;
	    }
	}
	closedir(DIR);	
	closedir(RFAMDIR);
    }elsif($mode eq "2"){
	#CMcompare everything with everything
	#fill model array and compare the first model with all other model but itself
	#compare all following models with all other models but itself and all models that have already been compared
	#always remove model from array once it has been compared with the others
	my @model_array;
	while (defined($file = readdir(DIR))) {
	    unless($file=~/^\./){
		push(@model_array,$file);
	    }
	}
	open(BEGIN,">$tempdir_path/begin$counter") or die "Can't create begin$counter: $!";
	close(BEGIN);
	#read in query_number
	open (QUERYNUMBERFILE, "<$tempdir_path/query_number")or die "Could not open $tempdir_path/query_number: $!\n";
	my $query_number=<QUERYNUMBERFILE>;
	close QUERYNUMBERFILE;
	my $query_counter=1;
	for(1..$query_number){
	    my $model="input"."$query_counter".".cm";
	    print "1Foreach: Model $model\n";
	    my $column_counter=$query_counter+1;
	    for($column_counter..$query_number){
		my $compare_model="input"."$column_counter".".cm";
		print "Foreach: 2Compare-Model $model\n";
		#we do not increment $counter, because we only produce one result file for all comparisons
		unless("$model" eq "$compare_model"){
		    print STDERR "$executable_dir/CMCompare $model_dir/$model $model_dir/$compare_model \>\>$tempdir_path/result$counter";
		    system("$executable_dir/CMCompare $model_dir/$model $model_dir/$compare_model \>\>$tempdir_path/result$counter")==0 or die print "cmcws: Execution failed: model $model with compare_model $compare_model - $!\n";
		    print "done: $model, $compare_model\n";
		    $column_counter++;
		}
		
	    }
	    $query_counter++;
	    #shift(@model_array);
	}      
	my $number_of_displayed_comparisons=100;
	my $cutoff="none";
	system("$executable_dir/output_to_html.pl $server $base_dir $tempdir_folder $counter $mode $number_of_displayed_comparisons $cutoff")==0 or die "cmcws: Execution failed: tempdir $tempdir_folder mode $mode error  - $!";
	open(DONE,">$tempdir_path/done$counter") or die "Can't create $tempdir_path/done$file: $!";
	close(DONE);
	closedir(DIR);
    }else{
	print STDERR "cmcws: error - cmcws was called without specifing mode parameter";
    }	
}
