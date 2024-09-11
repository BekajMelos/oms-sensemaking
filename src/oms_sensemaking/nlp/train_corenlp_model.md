# Training a custom CoreNLP model with the TrainingDataProcessor

## Use Doccano to label a text file
1. Run the following commands
```
docker pull doccano/doccano
docker container create --name doccano \
  -e "ADMIN_USERNAME=admin" \
  -e "ADMIN_EMAIL=admin@example.com" \
  -e "ADMIN_PASSWORD=password" \
  -v doccano-db:/data \
  -p 8000:8000 doccano/doccano
```
2. Run `docker container start doccano`
3. Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
4. After logging in, click Create, select Sequence Labeling, and fill out the text fields. Make sure to select "Use relation labeling"
5. To upload a dataset: Dataset > Actions > Import, then select TextFile, upload the file, then click Import
6. To add NER labels: Labels > Span > Actions > Create Label
7. To add relation labels: Labels > Relation > Actions > Create Label
8. To annotate the text file click Start Annotation
9. To add a label to a word or phrase, highlight it, and then select the label. 
10. To relate two labeled entities together, under "Label Types", toggle Span to Relation. Next, click on the entities to relate in the order that you want the relation direction to point.
11. To export the annotation as a `.jsonl` file: Dataset > Actions > Export Dataset, then select the file format and click Export. This will download the file as `all.jsonl` in your `Downloads` folder


[Video tutorial of how to use Doccano](https://drive.google.com/file/d/1JVm_CtbArfB4h2WZ9LvMO1oBN6-K1XZm/view?usp=share_link)
You can find the official steps on the [Doccano github](https://github.com/doccano/doccano?tab=readme-ov-file#docker)


## Follow thsese steps to use the TrainingDataProcessor to turn an annotated `.jsonl` file into a `.tsv` file suitable for training a custom CoreNLP Model
1. [Download CoreNLP 4.5.7](https://stanfordnlp.github.io/CoreNLP/download.html), and set the classpath variable in `~/.zshrc` by adding `export CLASSPATH=$CLASSPATH:<path-to-corenlp-download-directory>/stanford-corenlp-4.5.7/*:`
2. Install Stanza's CoreNLP Client by running `python src/oms_sensemaking/nlp/install_corenlp_client.py`. To check that it properly installed, run `cd && ls` and make sure that it is present as folder `stanza_corenlp` in your home directory.
3. Download a sample annotated [.jsonl file](https://drive.google.com/file/d/11axfbv7zpZEliiLxkCVsC2b-KTuf9wDq/view?usp=share_link) from the shared drive. Alternatively, generate your own annotation with [Doccano](https://github.com/doccano/doccano)
4. Run `python src/oms_sensemaking/nlp/training_data_processor.py --annotated-filepath <path-to-jsonl-file>`
5. Running the previous command should generate two files in `src/oms_sensemaking/nlp/training/data/` with names `ner_training.tsv` and `relations_training.tsv`. Upon opening the files, if using the sample `.jsonl` file from the drive, they should match the format/contents of the files of the same name in the shared drive: [ner_training.tsv](https://drive.google.com/file/d/1bbE3ECA5F9d1yxe8fn5gwb1oLDihs0ba/view?usp=share_link), [relations_training.tsv](https://drive.google.com/file/d/1TOsWSksD-PI1YTf-Fv5a4liUUX-kPAx9/view?usp=share_link). These are the files used to train the CoreNLP models.
6. Repeat steps 3-5, using a different `.jsonl` file for testing. You can find one [here](https://drive.google.com/file/d/1Tk9Xd7JJYjDaDqxIyVpsQOsZl0aGp-U6/view?usp=share_link) in the shared drive. This time, specify the new names of your testing `.tsv` files with `python src/oms_sensemaking/nlp/training_data_processor.py --annotated-filepath <path-to-jsonl-file> --ner-save-filepath <path-to-ner-test-file.tsv> --relation-save-filepath <path-to-relation-test-file.tsv>`

## Follow these steps to train a custom CoreNLP NER model
1. To train a custom CoreNLP NER model, run `java edu.stanford.nlp.ie.crf.CRFClassifier -prop src/oms_sensemaking/nlp/training/ner.prop`. The file `ner.prop` specifies the path to your training `.tsv` file, and the location to save your custom model to, which you can change if needed.
2. To test your custom CoreNLP NER model, run `java edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier src/oms_sensemaking/nlp/training/data/ner-model.ser.gz -testFile src/oms_sensemaking/nlp/training/data/<path-to-test-file>.tsv`. The output should show results that look like [these](https://tex.gerbil-cloud.ts.net:3000/oms/oms-bridge/src/branch/feature/sensemaking-exploration/omsb-sensemaker/docs/train_custom_model_for_corenlp.md#step-4-test-ner-model)
