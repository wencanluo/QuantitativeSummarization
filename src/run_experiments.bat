rem python CourseMirror_Survey.py CS0445 28

rem runSennaCourseMirror.bat CS0445 28

rem python word2vec_wrapper.py 
rem python QPS_prepare.py IE256 25 oracle_annotator_1 annotator1
rem python QPS_prepare.py IE256 25 oracle_annotator_2 annotator2
rem runLSA_All.bat IE256 25 oracle_annotator_1 annotator1
runLSA_All.bat IE256 25 oracle_annotator_2 annotator2

rem python word2vec_wrapper.py 
rem python QPS_prepare.py IE256_2016 26 oracle_annotator_1 annotator1
rem python QPS_prepare.py IIE256_2016 26 oracle_annotator_2 annotator2
rem runLSA_All.bat IE256_2016 26 oracle_annotator_1 annotator1
rem runLSA_All.bat IE256_2016 26 oracle_annotator_2 annotator2

rem run in linux only
rem python QPS_simlearning_getfeature.py IE256 25 oracle_annotator_1 annotator1
rem python QPS_simlearning_getfeature.py IE256 25 oracle_annotator_2 annotator2

rem python QPS_extraction.py CS0445 28 QPS_NP NP N
rem python QPS_prepare.py CS0445 28 QPS_NP syntax

rem python QPS_extraction.py IE256 25 QPS_combine combine N

rem python QPS_extraction.py IE256_2016 26 QPS_combine combine N

rem python QPS_prepare.py CS0445 28 QPS_NP crf

rem python eval_extraction.py CS0445

rem Finished phrase extraction for QPS_NP

rem runLSA_All.bat CS0445 28 QPS_NP syntax

rem for wapiti
rem python QPS_extraction.py IE256_2016 26 QPS_A1 annotator1 N
rem python QPS_extraction.py CS0445 28 QPS_A1 annotator1 N
rem python QPS_extraction.py IE256_2016 26 QPS_combine combine N
rem python QPS_extraction.py CS0445 28 QPS_combine combine N

rem step: extract crf phrase
rem python QPS_prepare.py IE256_2016 26 QPS_combine crf
rem step: get phrase similarity feature
rem runLSA_All.bat IE256_2016 26 QPS_combine crf

rem python QPS_prepare.py CS0445 28 QPS_combine crf
rem runLSA_All.bat CS0445 28 QPS_combine crf

@pause