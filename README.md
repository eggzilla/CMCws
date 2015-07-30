#![CMCompare Webserver](http://www.tbi.univie.ac.at/~egg/cmcws.png "CMCompare webserver") 
=========
If you have RNA-family models and want to compare them, the CMCompare webserver can help you.

RNA-family models can be formulated as covariance models. You can either compare your own uploaded set of covariance models among themselves, or against preexistent ones from Rfam. Rfam is a repository of curated RNA family models in covariance model (.cm) format.

ncRNA homology search:
Covariance models represent non-coding RNA families (miRNAs, tRNAs,..) and can be used to search for additional members of this family. You can use the model as input for cmsearch (part of the Infernal toolkit) to scan a genome of interest for possible new family members.

#![Search procedure](http://www.tbi.univie.ac.at/~egg/search_procedure_multiple_genomes.png "Search procedure")

The better a stretch of sequence fits to the covariance model, the higher the score.

Covariance model comparison:
If you have built your own covariance model it is useful to check what other models are already available in Rfam. CMCompare Webserver is based on CMCompare, which returns a link-score for every pair of models checked. A high link score can be an indicator for:

*  A model for the same RNA family is already present.
*  There is a possible lack of specificity between the the models, meaning that both score high for the same sequence.
*  There is a biological relationship between the models, that explains the overlap in specificity.

A tutorial and examples for cases like these can be found in [Help](http://nibiru.tbi.univie.ac.at/cmcws/help.html).

The Webserver has been published in the [Nucleic Acid Research Webserver Issue 2013](http://nar.oxfordjournals.org/content/early/2013/05/02/nar.gkt329).

Version history:

|Version|Git-commit|Date|Description|
|1.11|91|Thu July 30 21:19 2014 +0100|Added support for Rfam 12, fixed bugs resulting from new server infrastructure, added README.md|
|1.10|73|Tue Sep 3 13:00 2013 +0100|Fixed a bug with HMMs in input. Added links to publication. Increased upload file size limit to 1.5Mb.Updated Help and Introduction pages.|
|1.09|68|Tue Apr 29 23:00 2013 +0100|Added feature to define specific groups of Rfam models to compare against|
|1.08|66|Tue Apr 6 13:30 2013 +0100|Improved and expanded the help section for link score distribution|
|1.07|65|Tue Apr 2 20:15:08 2013 +0100|Added improvements based on reviewer comments|
|1.00|58|Thu Dec 27 13:28:08 2012 +0100|Stable Version|
|0.00|1|Sun Jan 29 21:04:25 2012|Development Version|
