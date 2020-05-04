#run this file in a separate window to use the cnlp server

current=$(pwd)
cnlp_dir=~/stanford-corenlp-full-2018-10-05;

if [ $1 = 'zh' ]
then
    lang="-serverProperties StanfordCoreNLP-chinese.properties"
elif [ $1 = 'es' ]
then
    lang="-serverProperties StanfordCoreNLP-spanish.properties"
elif [ $1 = 'de' ]
then
    lang="-serverProperties StanfordCoreNLP-german.properties"
else
    lang=""
fi

cd $cnlp_dir

# Run the server using all jars in the current directory (e.g., the CoreNLP home directory)
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 150000 $lang


cd $current #this line never actually runs