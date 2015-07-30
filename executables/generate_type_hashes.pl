#!/usr/bin/perl 
#Generates one table for each Rfam type containing all Rfam accession ids in the first column
#and 1 in the second column if the model has that type, 0 if not.
use warnings;
use strict;
use diagnostics;
use List::MoreUtils qw/uniq/;
#Input is path to file that should be split - can be found in data/Rfam_tables
my $input_filename=$ARGV[0];
#Input file description:
#the file for Rfam11 is the html table from Rfam (section browse)  http://rfam.sanger.ac.uk/families#A
#that has been converted into a csv
#colums(separated by ,)
#Original order,ID,Accession,Type,Seed,Full,Average length,Sequence,Description
#read all available types from the corresponding column
my @multiple_Rfam_types;
my @input;
open (INPUTFILE, "<$input_filename") or die "Cannot open input-file";
while(<INPUTFILE>){
    push (@input,$_);
}
close INPUTFILE;
print @input;
#all model counter tracks the total number of models
my $all_models_counter=0;
foreach my $line (@input){
    chomp($line);
    my @split_array = split(/,/,$line);
    $all_models_counter++;
    my @types=split(/;/,$split_array[3]);
    foreach my $type (@types){
	#we exclude the csv - header line 
	if($type=~/\w+/ && $type ne "Type"){
	    #we push everything on the type array and flatten it with uniqe afterwards
	    $type=~s/\s+//;
	    push(@multiple_Rfam_types,$type);
	}
    }   
}
my @unique_Rfam_types = uniq @multiple_Rfam_types;
#substract 1 from the model counter to consider the header line
$all_models_counter=$all_models_counter-1;
open (OVERVIEW, ">>types/overview") or die "Cannot write output file";
print OVERVIEW "All;$all_models_counter\n";
close OVERVIEW;

foreach my $unique_Rfam_type (@unique_Rfam_types){
    my $count=0;
    #type specific hash table
    open (OUTPUTFILE, ">types/$unique_Rfam_type") or die "Cannot write output file";
    foreach my $line (@input){
	chomp($line);
	my @split_array = split(/,/,$line);
	my $rfam_id=$split_array[2];
	$rfam_id=~s/\s//;
	if($line=~/$unique_Rfam_type/){
            my $output="$rfam_id\n";
	    #my $output="$rfam_id;1\n";
	    $count++;
	    print OUTPUTFILE "$output";
	}else{
	    #my $output="$rfam_id;0\n";
	    #print OUTPUTFILE "$output";
	}
	
    }
    close OUTPUTFILE;
    
    open (OVERVIEW, ">>types/overview") or die "Cannot write output file";
    #print typename and occurence number of the type to overview file
    print OVERVIEW "$unique_Rfam_type;$count\n";
    close OVERVIEW;  
}

