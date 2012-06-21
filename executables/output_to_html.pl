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
my $tempdir_input=$ARGV[0];
my $result_file_number_input=$ARGV[1];
my $mode=$ARGV[2];
my $number_of_hits=$ARGV[3];
my $cutoff=$ARGV[4];
my $model_name_1_string=$ARGV[5];
my $model_name_2_string=$ARGV[6];
my $file_input;
my $result_file_number;
#print STDERR "cmcws: output - parameters: tempdir: $tempdir_input, mode: $mode, number_of_hits: $number_of_hits, cutoff: $cutoff , model_name_1: $model_name_1_string , model_name_2: $model_name_2_string";
if(defined($result_file_number_input)){
    if(-e "$tempdir_input/result$result_file_number_input"){
	$result_file_number=$result_file_number_input;
	$file_input = "$tempdir_input/result$result_file_number_input";    
    }
}else{
    print STDERR "cmcws: output_to_html.pl executed with nonexistent inputfile: $tempdir_input/result$result_file_number_input\n";
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
my $highest_link_score;
my $lowest_link_score;
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
	#retrieve id numbers
	#determine link score
	my $link_score=min($split[2],$split[3]);
	unless(defined($highest_link_score)){$highest_link_score=$link_score;}
	unless(defined($lowest_link_score)){$lowest_link_score=$link_score;}
	if($link_score>$highest_link_score){
	    $highest_link_score=$link_score;
	}
	if($link_score<$lowest_link_score){
	    $lowest_link_score=$link_score;
	}
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
    #@sorted_entries=reverse(@reverse_sorted_entries);
    #write csv-file only if not present
    open(CSVOUTPUT,">$tempdir_input/csv$result_file_number") or die "Can't write $tempdir_input/csv$result_file_number: $!";
    print CSVOUTPUT "link_score;id1;id2;name1;name2;score1;score2;secondary_structure_1;secondary_structure_2;matching_nodes_1;matching_nodes_2;link_sequence\n";
    foreach(@sorted_entries){
	my @sorted_entry=@$_;
	my $joined_entry=join(";",@sorted_entry);
	print CSVOUTPUT "$joined_entry\n";
    }
    close CSVOUTPUT;
    
    if($mode eq "2"){
	#get number of keys in result matrix hash
	open (QUERYNUMBERFILE, "<$tempdir_input/query_number")or die "Could not open $tempdir_input/query_number: $!\n";
	my $number_of_entries=<QUERYNUMBERFILE>;
	close QUERYNUMBERFILE;
	#my $number_of_entries += scalar keys %result_matrix;
	#compute result matrix
	#we have a quadratic matrix, the number of lines determines i (lines) and j(columns)
	my $i=$number_of_entries;
	my $j=$number_of_entries;
	print STDERR "Lines i: $i , Columns j: $j\n";
	#prepare relative link score computation in percent
	my $link_score_difference= $highest_link_score - $lowest_link_score;
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
		    print STDERR "itself: $i_counter $j_counter\n";
		}elsif(defined($result_matrix{"$i_counter"."_"."$j_counter"})){
		    my $current_link_score=$result_matrix{"$i_counter"."_"."$j_counter"};
		    #compute background_color
		    my $background_color_string;
		    unless($link_score_difference==0){
			my $percent=(($current_link_score-$lowest_link_score)/$link_score_difference)*100;
			$background_color_string=&percent_to_rgb_color($percent);
		    }else{
			$background_color_string="";
		    }
		    $result_matrix_string.="<td style=\"border:solid 1px #000;$background_color_string;\"> $current_link_score </td>";
		    print STDERR "ij - $current_link_score : $i_counter"."_"."$j_counter\n";
		}else{
		    #compute background color
		    my $current_link_score=$result_matrix{"$j_counter"."_"."$i_counter"};
		    my $background_color_string;
		    unless($link_score_difference==0){
			my $percent=(($current_link_score-$lowest_link_score)/$link_score_difference)*100;
			$background_color_string=&percent_to_rgb_color($percent);
		    }else{
			$background_color_string="";
		    }
		    $result_matrix_string.="<td style=\"border:solid 1px #000;$background_color_string;\"> $current_link_score </td>";
		    print STDERR "ji - $current_link_score : $j_counter"."_"."$i_counter\n";
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
	open(RESULTMATRIX,">$tempdir_input/result_matrix") or die "Can't write $tempdir_input/result_matrix: $!";
	print RESULTMATRIX "$result_matrix_string";
	close RESULTMATRIX;
	#print STDERR Dumper(%result_matrix);
    }
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
    my $output_line;    
    if($model_name_filter_type eq "A"){
	#we push matching entries on new array
	if($name1=~/$model_name_1_string/g && $name2=~/$model_name_2_string/g){
	    print STDERR "\n A \n";
	    if($mode eq "1"){
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
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
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
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
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	    }else{
		$output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
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
	    $output_line ="\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
	}else{
	    $output_line = "\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$link_score"."</td>"."<td>"."$id1_truncated"."</td>"."<td>"."$name1"."</td>"."<td>"."$id2_truncated"."</td>"."<td>"."$name2"."</td>"."<td>"."$score1"."</td>"."<td>"."$score2"."</td>"."</tr>\n";
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

sub percent_to_rgb_color{
    #rgb represents the color spectrum with 3 values that can be set in percent in CSS
    #if we go through the spectrum from blue which corresponds with the blue channel set to 100%
    # to red, which corresponds with the red channel set to 100% we proceed as follows:
    #first set the blue channel to 100 percent. Then increase the green channel to 100% (cyan).
    #then lower the blue channel to 0%, this yields green. Increasing the red channel to 100% gives
    #orange and finally decreasing the green channel to 0% gives red. 
    my $percent_value=shift;
    my $blue;
    my $red;
    my $green;
    my $blue_output;
    my $red_output;
    my $green_output;
    if($percent_value<=25){
	#blue is 100%, red is 0% and green is being increased
	$green=($percent_value/25)*100;
	$green_output=printf '%3d',$green;
	$red_output=0;
	$blue_output=100;
    }elsif($percent_value>25 && $percent_value<=50){
	#blue is 100%, green is 100% red is 0% and blue is being decreased
	$blue=100-(($percent_value/50)*100);
	$blue_output=printf '%3d',$blue;
	$red_output=0;
	$green_output=100;
    }elsif($percent_value>50 && $percent_value<=75){
	#blue is 0%, green is 100% red is 0% and red is being increased
	$red=($percent_value/75)*100;
	$red_output=printf '%3d',$red;
	$green_output=100;
	$blue_output=0;
    }else{
	#blue is 0%, green is 100% red is 100% and green is being decreased
	$green=100-($percent_value/100)*100;
	$green_output=printf '%3d',$green;
	$red_output=100;
	$blue_output=0;
    }
    my $return_string="background-color:rgb($red_output\%,$green_output\%,$blue_output\%)";
    return $return_string;
}
