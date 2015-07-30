#![CMCompare Webserver](http://www.tbi.univie.ac.at/~egg/cmcws.png "CMCompare webserver") 
=========
If you have RNA-family models and want to compare them, the CMCompare webserver can help you.

RNA-family models can be formulated as covariance models. You can either compare your own uploaded set of covariance models among themselves, or against preexistent ones from Rfam. Rfam is a repository of curated RNA family models in covariance model (.cm) format.

ncRNA homology search:
Covariance models represent non-coding RNA families (miRNAs, tRNAs,..) and can be used to search for additional members of this family. You can use the model as input for cmsearch (part of the Infernal toolkit) to scan a genome of interest for possible new family members.

[Search procedure](http://www.tbi.univie.ac.at/~egg/search_procedure_multiple_genomes.png "Search procedure")

The better a stretch of sequence fits to the covariance model, the higher the score.

Covariance model comparison:
If you have built your own covariance model it is useful to check what other models are already available in Rfam. CMCompare Webserver is based on CMCompare, which returns a link-score for every pair of models checked. A high link score can be an indicator for:

    A model for the same RNA family is already present.
    There is a possible lack of specificity between the the models, meaning that both score high for the same sequence.
    There is a biological relationship between the models, that explains the overlap in specificity.

A tutorial and examples for cases like these can be found in [Help](http://nibiru.tbi.univie.ac.at/cmcws/help.html).

The Webserver has been published in the [Nucleic Acid Research Webserver Issue 2013](http://nar.oxfordjournals.org/content/early/2013/05/02/nar.gkt329).
