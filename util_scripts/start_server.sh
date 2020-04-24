#run this file in a separate window to use the cnlp server

current=$(pwd)
cnlp_dir=~/stanford-corenlp-full-2018-10-05;

cd $cnlp_dir

# Run the server using all jars in the current directory (e.g., the CoreNLP home directory)
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 150000


cd $current #this line never actually runs