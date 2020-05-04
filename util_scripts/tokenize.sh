# params must be FULL PATHS
# CoreNLP server must be on
#
# $1 = path to article text file
# $2 = save directory
#
# Run example:
# ./tokenize.sh ~/code/proj/ppr/demo/articles/name.txt ~/code/proj/ppr/demo/tokenized

#cnlp_dir=~/stanford-corenlp-full-2018-10-05;
current=$(pwd);

f=$(basename $1)
save="${f%.*}"
echo $save
#cp $f $cnlp_dir;
#mv $f .$f #hide the file as a way to checkpoint progress

text=$(cat $1) #get the text to send to the server

#cd $cnlp_dir

data=$(wget --post-data "$text" 'localhost:9000/?properties={"annotators":"ner","outputFormat":"json"}' -O -)

cd $2
echo $data > $save.json
cd $current