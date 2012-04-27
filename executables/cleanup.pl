#!/usr/bin/perl 
#cleans tempdir folder and removes all files excluding accounting and error log 
use warnings;
use strict;
use diagnostics;
use File::stat;
use Sys::Hostname;
use Time::localtime;
print STDERR "cmcws: launched cleanup\n";
#Input is path to file that should be split
my $tempdir_input=$ARGV[0];
my $tempdir;
my $month;
my $file;    
my $host = hostname;

#tempdir
if(defined($tempdir_input)){
    if(-e "$tempdir_input"){
	$tempdir = $tempdir_input;    
    }
}else{

}
#get current month
#my ($sec,$min,$hour,$day,$current_month,$yr19,@rest) = localtime(time);
#my $date= (($yr19+1900)."-".sprintf("%02d",++$month)."-".sprintf("%02d",$day)." ".sprintf("%02d",$hour).":".sprintf("%02d",$min).":".sprintf("%02d",$sec));
my $current_month= localtime->mon() + 1;
my $previous_month=$current_month-1;
my $two_months_ago=$current_month-2;
if($current_month==1){
    $previous_month=12;
    $two_months_ago=11;
}

if($current_month==2){
    $previous_month=1;
    $two_months_ago=12;
}

#convert month via Hash
my %month_text_to_number=(
    Jan => '1',
    Feb => '2',
    Mar => '3',
    Apr => '4',
    May => '5',
    Jun => '6',
    Jul => '7',
    Aug => '8',
    Sep => '9',
    Oct => '10',
    Nov => '11',
    Dec => '12',
    );


#todo create progress indicators
if(defined($tempdir)){
    chdir($tempdir);
    opendir(DIR, $tempdir) or die "can't opendir $tempdir: $!";
    while (defined($file = readdir(DIR))) {
	unless($file=~/^\./ or $file=~/^accounting/ or  $file=~/^error/){
	    #check that file is older than specified number of month
	    my $timestamp = ctime(stat($file)->mtime);
	    my @time_elements=split(/ /,$timestamp);
	    my $month_text=$time_elements[1];
	    my $month_number=$month_text_to_number{$month_text};
	    unless($month_number==$current_month or $month_number==$previous_month or $two_months_ago==$current_month){
		print "File: $file - Timestamp: $timestamp\n";
		print "Month : $month_text - $month_number\n";
		#system("rm -rf $file")==0 or die "cmcws: Cleanup-deletion failed: Directory $file - $!\n";
		print "rm -rf $file\n";
	    }
	}
    }
}

print "Hostname: $host $current_month \n";
