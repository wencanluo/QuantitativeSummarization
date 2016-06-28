path=../data/IE256_2016/QPS_NP/phrase
dest=../data/IE256_2016/QPS_NP/phrase

for i in $(seq 1 1 26)
do
    #mkdir $dest/$i/
    #cp $path/$i/*.cache.json $dest/$i
    cp $path/$i/q1.syntax.cache.json $dest/$i/q1.crf.cache.json
    cp $path/$i/q2.syntax.cache.json $dest/$i/q2.crf.cache.json
    
    #mv $dest/$i/q1.syntax.cache.json $dest/$i/q1.annotator1.cache.json
    #mv $dest/$i/q2.syntax.cache.json $dest/$i/q2.annotator1.cache.json
    #cp $path/$i/*.ref.summary $dest/$i
    #cp $path/$i/*.L30.summary $dest/$i
done

