path=../data/IE256/oracle_annotator_1/phrase
dest=../data/IE256/oracle_annotator_2/phrase

for i in $(seq 14 1 25)
do
    #mkdir $dest/$i/
    cp $path/$i/*.cache.json $dest/$i
    #mv $dest/$i/q1.crf.cache.json $dest/$i/q1.annotator2.cache.json
    #mv $dest/$i/q2.crf.cache.json $dest/$i/q2.annotator2.cache.json
    #cp $path/$i/*.ref.summary $dest/$i
    #cp $path/$i/*.L30.summary $dest/$i
done

