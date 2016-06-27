path=../data/IE256_2016/oracle_annotator_1/phrase
dest=../data/IE256_2016/oracle_annotator_2/phrase

for i in $(seq 1 1 26)
do
    #mkdir $dest/$i/
    cp $path/$i/*.cache.json $dest/$i
    #mv $dest/$i/q1.syntax.cache.json $dest/$i/q1.annotator1.cache.json
    #mv $dest/$i/q2.syntax.cache.json $dest/$i/q2.annotator1.cache.json
    #cp $path/$i/*.ref.summary $dest/$i
    #cp $path/$i/*.L30.summary $dest/$i
done

