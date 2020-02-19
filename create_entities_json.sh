cnlp_dir=~/stanford-corenlp-full-2018-10-05;
current=$(pwd);
cp $1 $cnlp_dir;
cd $cnlp_dir;

java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP \
-annotators tokenize,ssplit,pos,lemma,ner \
-file $1 \
-outputFormat json;

mv $1.json ~/code/proj/ppr/$1.json;
cd $current;