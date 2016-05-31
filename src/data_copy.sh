path=../data/IE256/QPS_A2_N/phrase
dest=../data/IE256/QPS_NP/phrase

for i in $(seq 14 1 25)
do
    #mkdir $dest/$i/
    cp $path/$i/*.cache.json $dest/$i
    mv $dest/$i/q1.crf.cache.json $dest/$i/q1.syntax.cache.json
    mv $dest/$i/q2.crf.cache.json $dest/$i/q2.syntax.cache.json
    #cp $path/$i/*.ref.summary $dest/$i
    #cp $path/$i/*.L30.summary $dest/$i
done

