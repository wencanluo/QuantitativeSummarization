set cid=%1
set maxLecture=%2
set system=%3
set method=%4
java -jar optimalLSA.jar ../../SEMILAR/data/ ../data/%cid%/%system%/phrase/ %maxLecture% %method%