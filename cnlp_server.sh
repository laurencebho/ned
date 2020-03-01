cnlp_dir=~/stanford-corenlp-full-2018-10-05;
current=$(pwd);
cp $1.txt $cnlp_dir;
cd $cnlp_dir;

data=$(wget --post-data '$1' 'localhost:9000/?properties={"annotators":"ner","outputFormat":"json"}' -O -)
cd $current;
echo $data > $1.json