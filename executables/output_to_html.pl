#!/usr/bin/perl 
#transforms aggregated CMCompare output to .html file
use warnings;
use strict;
use diagnostics;
use Math::Round;
use List::Util qw[min max];
#use Data::Dumper;
#invocation from tempdir: ../../executables/output_to_html.pl /srv/http/cmcws/html/J_KsXXLTAK 1 1 10 20
#get input and assemble it into datastructure, return list of x best interactions
my $server=$ARGV[0];
my $base_dir=$ARGV[1];
my $tempdir_folder=$ARGV[2];
my $tempdir_path="$base_dir"."/$tempdir_folder";
my $result_file_number_input=$ARGV[3];
my $mode=$ARGV[4];
my $number_of_hits=$ARGV[5];
my $cutoff=$ARGV[6];
my $model_name_1_string=$ARGV[7];
my $model_name_2_string=$ARGV[8];
my $file_input;
my $result_file_number;
#print STDERR "cmcws: output - parameters: tempdir: $tempdir_path, mode: $mode, number_of_hits: $number_of_hits, cutoff: $cutoff , model_name_1: $model_name_1_string , model_name_2: $model_name_2_string";
if(defined($result_file_number_input)){
    if(-e "$tempdir_path/result$result_file_number_input"){
	$result_file_number=$result_file_number_input;
	$file_input = "$tempdir_path/result$result_file_number_input";    
    }
}else{
    print STDERR "cmcws: output_to_html.pl executed with nonexistent inputfile: $tempdir_path/result$result_file_number_input\n";
}

if(defined($mode)){
    if($mode eq "1"){
	$mode = 1;
    }elsif($mode eq "2"){
	$mode = 2;
    }
}else{
    $mode = 0;
}

#If csv file is present we read directly from there
my @entries;
my @sorted_entries;
my @reverse_sorted_entries;
my %result_matrix;
unless(-e "$tempdir_path/csv$result_file_number"){
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
	#retrieve id numbers
	#determine link score
	my $link_score=min($split[2],$split[3]);
	my $link_sequence=$split[4];
	if($mode eq "2"){
	    #retrieve id numbers
	    my $id1_truncated=$id1;
	    $id1_truncated=~s/.cm//;
	    my $id1_number= $id1_truncated;
	    $id1_number=~s/input//;
	    my $id2_truncated=$id2;
	    $id2_truncated=~s/.cm//;
	    my $id2_number= $id2_truncated;
	    $id2_number=~s/input//;
	    #add entry to result matrix hash
	    $result_matrix{ "$id1_number"."_"."$id2_number" } = "$link_score";
	}
	#link_score,id1,id2,name1,name2,score1,score2,secondary_structure_1,secondary_structure_2,matching_nodes_1,matching_nodes_2,link_sequence
	unless(-e "tempdir_path/inputidname$result_file_number"){
	    open(INPUTIDNAME,">$tempdir_path/inputidname$result_file_number") or die "Can't write : $!";
	    print INPUTIDNAME "$id1;$name1";
	    close INPUTIDNAME;
	}
	my @entry=($link_score,$id1,$id2,$name1,$name2,$split[2],$split[3],$split[5],$split[6],$split[7],$split[8],$split[4]);
	my $entry_reference=\@entry;
	push(@entries,$entry_reference);
    }
    close(INPUTFILE);
    #sort hash of array by maximin-score
    @sorted_entries = sort { $b->[0] <=> $a->[0] } @entries;
    #write csv-file only if not present
    open(CSVOUTPUT,">$tempdir_path/csv$result_file_number") or die "Can't write $tempdir_path/csv$result_file_number: $!";
    print CSVOUTPUT "link_score;id1;id2;name1;name2;score1;score2;secondary_structure_1;secondary_structure_2;matching_nodes_1;matching_nodes_2;link_sequence\n";
    foreach(@sorted_entries){
	my @sorted_entry=@$_;
	my $joined_entry=join(";",@sorted_entry);
	print CSVOUTPUT "$joined_entry\n";
    }
    close CSVOUTPUT;
    
    if($mode eq "2"){
	#get number of keys in result matrix hash
	open (QUERYNUMBERFILE, "<$tempdir_path/query_number")or die "Could not open $tempdir_path/query_number: $!\n";
	my $number_of_entries=<QUERYNUMBERFILE>;
	close QUERYNUMBERFILE;
	#my $number_of_entries += scalar keys %result_matrix;
	#compute result matrix
	#we have a quadratic matrix, the number of lines determines i (lines) and j(columns)
	my $i=$number_of_entries;
	my $j=$number_of_entries;
	print STDERR "Lines i: $i , Columns j: $j\n";
	#prepare relative link score computation in percent
	my $result_matrix_string="<tr>
	<td style=\"text-align:left;\">Matrix of result linkscores for all models: <a href=\"#\" onmouseover=\"XBT(this, {id:'1'})\"><img style=\"vertical-align:middle;border:solid 0px #000;\" src=\"pictures/info.png\" alt=\"Info\"></a></td>
	<td colspan=\"2\"> </td>
	<td> </td>
	</tr>
	<tr>
	<td colspan=\"4\" style=\"text-align:left;border:solid 1px #000;\">
	  <table style=\"display:none;\">
	    <tr><td> <table>";
	#add index row for x-axis
	$result_matrix_string.="<tr>";
	my $index_counter=0;
	for(0..$i){
	    if($index_counter==0){
		$result_matrix_string.="<td></td>";
	    }else{
		$result_matrix_string.="<td> Model $index_counter </td>";
	    }
	    $index_counter++;
	}
	my $i_counter=1;
	for(1..$i){
	    #produce tablerow and index field for y-axis
	    $result_matrix_string.="<tr><td>Model $i_counter</td>";
	    my $j_counter=1;
	    for(1..$j){
		#lookup link_scores and compute rgb-color
		if($i_counter eq $j_counter){
		    #this equals comparsion of the model against iteself, we set value to x and background to white
		    $result_matrix_string.="<td style=\"border:solid 1px #000;\"> x </td>";
		    #print STDERR "itself: $i_counter $j_counter\n";
		}elsif(defined($result_matrix{"$i_counter"."_"."$j_counter"})){
		    my $current_link_score=$result_matrix{"$i_counter"."_"."$j_counter"};
		    #compute background_color
		    my $background_color_string;
		    $background_color_string=&linkscore_to_rgb_color($current_link_score);
		    $result_matrix_string.="<td style=\"border:solid 1px #000;$background_color_string;\"> $current_link_score </td>";
		    #print STDERR "ij - $current_link_score : $i_counter"."_"."$j_counter\n";
		}else{
		    #compute background color
		    my $current_link_score=$result_matrix{"$j_counter"."_"."$i_counter"};
		    my $background_color_string;
		    $background_color_string=&linkscore_to_rgb_color($current_link_score);
		    $result_matrix_string.="<td style=\"border:solid 1px #000;$background_color_string;\"> $current_link_score </td>";
		    #print STDERR "ji - $current_link_score : $j_counter"."_"."$i_counter\n";
		}
		$j_counter++;
	    }
	    $result_matrix_string.="</tr>";
	    $i_counter++;
	}
	$result_matrix_string.="</table>
	  </td></tr>
	  </table>
	  <p class=\"demo5 expIco\">Show</p>
	  </td>
	</tr>";
	open(RESULTMATRIX,">$tempdir_path/result_matrix") or die "Can't write $tempdir_path/result_matrix: $!";
	print RESULTMATRIX "$result_matrix_string";
	close RESULTMATRIX;
	#print STDERR Dumper(%result_matrix);
    }
}else{
    #csv is already present, we read it in
    open(CSVINPUT,"<$tempdir_path/csv$result_file_number") or die "Can't write $tempdir_path/csv$result_file_number: $!";
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
    if($cutoff eq "none"){
	push(@filtered_sorted_entries,$_);
    }else{
	if($sorted_entry[0]>=$cutoff){
	    print STDERR "Entry1: $sorted_entry[0] Entry2: $sorted_entry[2] Cutoff: $cutoff\n";
	    push(@filtered_sorted_entries,$_);
	}else{
	    #print STDERR "cmcws: Entry1: $sorted_entry[0] Entry2: $sorted_entry[2] Cutoff: $cutoff\n";
	}
    }
}

#Filter 2 number of hits

if(@filtered_sorted_entries>$number_of_hits){
    #throw away overhead
    my $index_number=$number_of_hits-1;
    @filtered_sorted_entries=@filtered_sorted_entries[0..$index_number];


}

#decide which kind of filter to apply for model names 
my $model_name_filter_type;
if(defined($model_name_1_string) && $model_name_1_string ne "none" && defined($model_name_2_string) && $model_name_2_string ne "none"){
    $model_name_filter_type="A";
}elsif(defined($model_name_1_string) && $model_name_1_string ne "none"){
    $model_name_filter_type="B";
}elsif(defined($model_name_2_string) && $model_name_2_string ne "none"){
    $model_name_filter_type="C";
}else{
    $model_name_filter_type="D";
}

#create output html with x-hits
my $counter=1;
open (FILTEREDTABLE, ">$tempdir_path/filtered_table$result_file_number") or die "Cannot open filtered_table$result_file_number: $!";
open (FILTEREDCSV, ">$tempdir_path/csv_filtered$result_file_number") or die "Cannot open csv_filtered$result_file_number: $!";
my $graph_output="graph g {\n";
foreach(@filtered_sorted_entries){
    my @filtered_sorted_entry=@$_;
    my $filtered_csv_output=join(" ",@filtered_sorted_entry);
    print FILTEREDCSV "$filtered_csv_output";
    my $link_score=$filtered_sorted_entry[0];
    my $id1=$filtered_sorted_entry[1];
    my $id1_truncated=$id1;
    $id1_truncated=~s/.cm//;
    my $id1_number=$id1_truncated;
    $id1_number=~s/input//;
    my $id2=$filtered_sorted_entry[2];
    my $id2_truncated=$id2;
    $id2_truncated=~s/.cm//;
    my $id2_number=$id2_truncated;
    $id2_number=~s/input//;
    my $name1=$filtered_sorted_entry[3];
    my $name2=$filtered_sorted_entry[4];
    my $score1=$filtered_sorted_entry[5];
    my $score2=$filtered_sorted_entry[6];
    my $secondary_structure1=$filtered_sorted_entry[7];
    my $secondary_structure2=$filtered_sorted_entry[8];
    my $link_sequence=$filtered_sorted_entry[11];
    my $rounded_link_score=nearest(1, $link_score);
    #Filter 3 show only hit containing rfamname in rfam name
    my $output_line;    
    my $href="$server/cmcws.cgi?page=3&mode=$mode&tempdir=$tempdir_folder&result_number=$result_file_number_input&identifier="."$id1_number"."_"."$id2_number";
    if($model_name_filter_type eq "A"){
	#we push matching entries on new array
	if($name1=~/$model_name_1_string/g && $name2=~/$model_name_2_string/g){
	    print STDERR "\n A \n";
	    if($mode eq "1"){
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\"></a>"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\"></a>"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }
	    print FILTEREDTABLE "$output_line";
	    $counter++;
	    #construct result graph
	    $graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n"; 
	}
    }elsif($model_name_filter_type eq "B"){
	print STDERR "\n B \n";
	#we push matching entries on new array
	if($name1=~/$model_name_1_string/g){
	    if($mode eq "1"){
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\"></a>"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }
	    print FILTEREDTABLE "$output_line";
	    $counter++;
	    #construct result graph
	    $graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n"; 
	}
    }elsif($model_name_filter_type eq "C"){
	print STDERR "\n C \n";
	if($name2=~/$model_name_2_string/g){
	    print STDERR "\n cmcws: accepted name2 $name2: model_name2: $model_name_2_string\n";
	    if($mode eq "1"){
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\"></a>"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }
	    print FILTEREDTABLE "$output_line";
	    $counter++;
	    #construct result graph
	    $graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n"; 
	}else{
	    print STDERR "\n cmcws: rejected name2 $name2: model_name2: $model_name_2_string\n";
	}
    }else{
	if($mode eq "1"){
	    $output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\"></a>"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	}else{
	    $output_line = "\<tr id\=\"t"."$counter\"\>"."<td>"."<a href=\"$href\"><img src=\"./pictures/magnifying_glass.png\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	}
	print FILTEREDTABLE "$output_line";
	$counter++;
	#construct result graph
	$graph_output.="\"$id2_truncated\\n$name2\" -- \"$id1_truncated\\n$name1\"  [label = \"$rounded_link_score\"];\n";
    }
}
close FILTEREDTABLE;
close FILTEREDCSV;
$graph_output.="}\n";
open (GRAPHOUT, ">$tempdir_path/graph_out$result_file_number.dot") or die "Cannot open graph_out$result_file_number: $!";
print GRAPHOUT "$graph_output";
close GRAPHOUT;
#print STDERR "cmcws: output_to_html.pl - cat $tempdir_path/graph_out$result_file_number.dot | circo -Tpng > $tempdir_path/graph$result_file_number.png\n";
`cat $tempdir_path/graph_out$result_file_number.dot | circo -Tpng > $tempdir_path/graph$result_file_number.png`;
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

sub linkscore_to_rgb_color{
    #linkscore over 20 red
    #linkscore between 10 and 20 orange
    #linkscore between 5 and 10 yellow
    #linkscore between 0 and 5 white
    #linkscore below 0 blue
    my $linkscore=shift;
    my $blue_output;
    my $red_output;
    my $green_output;
    if($linkscore>=20){
	$green_output=0;
	$red_output=100;
	$blue_output=0;
    }elsif($linkscore>=10 && $linkscore<20){
	$blue_output=0;
	$red_output=100;
	$green_output=65;
    }elsif($linkscore>=5 && $linkscore<10){
	$red_output=100;
	$green_output=100;
	$blue_output=0;
    }elsif($linkscore>=0 && $linkscore<5){
	$green_output=100;
	$red_output=100;
	$blue_output=100;
    }else{
	#linkscore under 0
	$green_output=0;
	$red_output=0;
	$blue_output=100;
    }
    my $return_string="background-color:rgb($red_output\%,$green_output\%,$blue_output\%)";
    return $return_string;
}
