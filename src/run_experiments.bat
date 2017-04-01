rem python CourseMirror_Survey.py CS0445 28

rem runSennaCourseMirror.bat CS0445 28

rem python QPS_prepare.py CS0445 28 QPS_NP syntax

rem python QPS_extraction.py CS0445 28 QPS_NP NP N

rem python QPS_extraction.py IE256 25 QPS_combine combine N

rem python QPS_extraction.py IE256_2016 26 QPS_combine combine N

rem python QPS_prepare.py CS0445 28 QPS_NP crf

rem python eval_extraction.py CS0445

rem Finished phrase extraction for QPS_NP

rem runLSA_All.bat CS0445 28 QPS_NP syntax

rem for wapiti
python QPS_extraction.py IE256_2016 26 QPS_combine combine N
python QPS_extraction.py CS0445 28 QPS_combine combine N

@pause