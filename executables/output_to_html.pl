#!/usr/bin/perl 
#transforms aggregated CMCompare output to .html file
use warnings;
use strict;
use diagnostics;
use Math::Round;
use List::Util qw[min max];
#invocation from tempdir: ../../executables/output_to_html.pl /srv/http/cmcws/html/J_KsXXLTAK 1 1 10 20
#get input and assemble it into datastructure, return list of x best interactions
my $tempdir_input=$ARGV[0];
my $result_file_number_input=$ARGV[1];
my $mode_input=$ARGV[2];
my $number_of_hits=$ARGV[3];
my $cutoff=$ARGV[4];
my $rfam_name_string=$ARGV[5];
my $file_input;
my $result_file_number;

if(defined($result_file_number_input)){
    if(-e "$tempdir_input/result$result_file_number_input"){
	$result_file_number=$result_file_number_input;
	$file_input = "$tempdir_input/result$result_file_number_input";    
    }
}else{
    print STDERR "cmcws: output_to_html.pl executed with nonexistent inputfile: $tempdir_input/result$result_file_number_input\n";
}

#If csv file is present we read directly from there
my @entries;
my @sorted_entries;
unless(-e "$tempdir_input/csv$result_file_number"){
    #define array of arrays
    print STDERR "cmcws: output_to_html.pl - Processing csv for all entries\n";
    open(INPUTFILE,"<$file_input") or die "Can't read $file_input: $!";
    while(<INPUTFILE>){
	chomp;
	#/srv/http/cmcws/html/J_KsXXLTAK/covariance_model/input1.cm   /srv/http/cmcws/data/Rfam10.1/RF00088.cm     -7.198     -6.415 ACUAUU ...... ...... [54,55,56,57,58,59,60] [65,66,67,68,69,70,71]
	my @split=split(/\s+/,$_);
	#use file names to retrieve model name
	my $name1=&model_name($split[0]);
	my $name2=&model_name($split[1]);
	my @split_name1=split(/\//,$split[0]);
	#use file names to retrieve model id
	my $id1=pop(@split_name1);
	my @split_name2=split(/\//,$split[1]);
	my $id2=pop(@split_name2);
	#determine link score
	my $link_score=min($split[2],$split[3]);
	my $link_sequence=$split[4];
	#linkscore,id1,id2,name1,name2,score1,score2,secondary_structure_1,secondary_structure_2,matching_nodes_1,matching_nodes_2,link_sequence
	unless(-e "tempdir_input/inputidname$result_file_number"){
	     open(INPUTIDNAME,">$tempdir_input/inputidname$result_file_number") or die "Can't write : $!";
	     print INPUTIDNAME "$id1;$name1";
	     close INPUTIDNAME;
	}
	my @entry=($link_score,$id1,$id2,$name1,$name2,$split[2],$split[3],$split[5],$split[6],$split[7],$split[8],$split[4]);
	my $entry_reference=\@entry;
	#remove elements that are below the cutoff
	#if($link_score>=$cutoff){
	push(@entries,$entry_reference);
	#}else{
	#print "Cutoff:@entry\n";
	#}
    }
    close(INPUTFILE);
    #sort hash of array by maximin-score
    @sorted_entries = sort { $b->[0] <=> $a->[0] } @entries;
    #write csv-file only if not present
    open(CSVOUTPUT,">$tempdir_input/csv$result_file_number") or die "Can't write $tempdir_input/csv$result_file_number: $!";
    print CSVOUTPUT "linkscore;id1;id2;name1;name2;score1;score2;secondary_structure_1;secondary_structure_2;matching_nodes_1;matching_nodes_2;link_sequence\n";
    foreach(@sorted_entries){
	my @sorted_entry=@$_;
	my $joined_entry=join(";",@sorted_entry);
	print CSVOUTPUT "$joined_entry\n";
    }
    close CSVOUTPUT;
}else{
    #csv is already present, we read it in
    open(CSVINPUT,"<$tempdir_input/csv$result_file_number") or die "Can't write $tempdir_input/csv$result_file_number: $!";
    while(<CSVINPUT>){
	my @entry=split(/;/,$_);
	my $entry_reference=\@entry;
	push(@sorted_entries,$entry_reference);
    }
    #get rid of the header line
    shift(@sorted_entries);
    close CSVINPUT;
}
#Filter 1 cutoff
print STDERR "cmcws: output_to_html.pl - Applying filters";
my @filtered_sorted_entries;
foreach (@sorted_entries){
    my @sorted_entry=@$_;
    if($sorted_entry[0]>=$cutoff){
	 print "Entry1: $sorted_entry[0] Entry2: $sorted_entry[2] Cutoff: $cutoff\n";
	 print "0";
	push(@filtered_sorted_entries,$_);
    }else{
	 print STDERR "cmcws: Entry1: $sorted_entry[0] Entry2: $sorted_entry[2] Cutoff: $cutoff\n";
    }
}

#Filter 2 number of hits

if(@filtered_sorted_entries>$number_of_hits){
    #throw away overhead
    my $index_number=$number_of_hits-1;
    @filtered_sorted_entries=@filtered_sorted_entries[0..$index_number];
}

#create output html with x-hits
my $counter=1;
open (FILTEREDTABLE, ">$tempdir_input/filtered_table$result_file_number") or die "Cannot open filtered_table$result_file_number: $!";
open (FILTEREDCSV, ">$tempdir_input/csv_filtered$result_file_number") or die "Cannot open csv_filtered$result_file_number: $!";
my $graph_output="graph g {\n";
foreach(@filtered_sorted_entries){
    my @filtered_sorted_entry=@$_;
    my $filtered_csv_output=join(" ",@filtered_sorted_entry);
    print FILTEREDCSV "$filtered_csv_output";
    my $link_score=$filtered_sorted_entry[0];
    my $id1=$filtered_sorted_entry[1];
    my $id1_truncated=$id1;
    $id1_truncated=~s/.cm//;
    my $id2=$filtered_sorted_entry[2];
    my $id2_truncated=$id2;
    $id2_truncated=~s/.cm//;
    my $name1=$filtered_sorted_entry[3];
    my $name2=$filtered_sorted_entry[4];
    my $score1=$filtered_sorted_entry[5];
    my $score2=$filtered_sorted_entry[6];
    my $secondary_structure1=$filtered_sorted_entry[7];
    my $secondary_structure2=$filtered_sorted_entry[8];
    my $link_sequence=$filtered_sorted_entry[11];
    my $rounded_link_score=nearest(1, $link_score);
    #Filter 3 show only hit containing rfamname in rfam name
    if(defined($rfam_name_string)){
	#we push matching entries on new array
	if($name2=~/$rfam_name_string/g){
	    print STDERR "cmcws: matched - $name2 with $rfam_name_string\n";
	    my $output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    print FILTEREDTABLE "$output_line";
	    $counter++;
	    #construct result graph
	    $graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n"; 
	}
    }else{
	my $output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	print FILTEREDTABLE "$output_line";
	$counter++;
	#construct result graph
	$graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n";
    }
}
close FILTEREDTABLE;
close FILTEREDCSV;
$graph_output.="}\n";
open (GRAPHOUT, ">$tempdir_input/graph_out$result_file_number.dot") or die "Cannot open graph_out$result_file_number: $!";
print GRAPHOUT "$graph_output";
close GRAPHOUT;
#print STDERR "cmcws: output_to_html.pl - cat $tempdir_input/graph_out$result_file_number.dot | circo -Tpng > $tempdir_input/graph$result_file_number.png\n";
`cat $tempdir_input/graph_out$result_file_number.dot | circo -Tpng > $tempdir_input/graph$result_file_number.png`;
#print "$graph_output";
close GRAPHOUT;
#get model name
sub model_name{
    my $input_filename=shift;
    open (MODELFILE, "<$input_filename") or die "Cannot open $input_filename: $!";
    my $name;
    while(<MODELFILE>){
	chomp;
	#look for name
	#todo: set default name if we hit end of alignment/cm and do not detect name 
	if($_=~/^NAME/){
	    my @split_array = split(/\s+/,$_);
	    my $last_element = @split_array - 1;
	    $name=$split_array[$last_element];
	}
    }
    close MODELFILE;
    if($name eq ""){
	$name="unnamed_model";
    }
    return $name;
}
