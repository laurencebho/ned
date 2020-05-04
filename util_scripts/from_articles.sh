# params must be FULL PATHS
# CoreNLP server must be on
#
# $1 = dataset directory i.e. dir of wikipedia text files
# $2 = save directory
#
# Run example:
# ./from_articles.sh ~/code/proj/ppr/run_outputs/en_articles ~/code/proj/ppr/run_outputs/en_jsons

cnlp_dir=~/stanford-corenlp-full-2018-10-05;
current=$(pwd);

cd $1
echo *
for f in *
do
    echo 'file is'
    echo $f
    save="${f%.*}"
    echo $save
    echo 'we are in'
    echo $(pwd)
    cp $f $cnlp_dir;
    #mv $f .$f #hide the file as a way to checkpoint progress

    text=$(cat $f) #get the text to send to the server

    cd $cnlp_dir
    echo 'now we are in'
    echo $(pwd)

    data=$(wget --post-data "$text" 'localhost:9000/?properties={"annotators":"ner","outputFormat":"json"}' -O -)
    #rm $f
    cd $2
    echo $data > $save.json
    cd $1
done