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
5. If you used a one-line `.jsonl` file, running the previous command should generate files in `src/oms_sensemaking/nlp/training/` with names `ner_1.tsv` and `relation_1.tsv`.
- Else if you used a two-line or `.jsonl` file, running the previous command should generate files in `src/oms_sensemaking/nlp/training/` with names `ner_1.tsv` and `relation_1.tsv`, `ner_2.tsv` and `relation_2.tsv`, etc. for each line in the `.jsonl` file.
- Upon opening the files, they should match the format/contents of the files of the same name in the [shared drive](https://drive.google.com/drive/folders/1VYO13pXthft8mB5TZwnsmuazHBJi0IB_?usp=share_link) if you used the sample `.jsonl` files. These resulting `.tsv` files are the files used to train the CoreNLP model.
6. Repeat steps 3-5, using a different `.jsonl` file for testing. You can find one [here](https://drive.google.com/file/d/1Tk9Xd7JJYjDaDqxIyVpsQOsZl0aGp-U6/view?usp=share_link) in the shared drive. This time, specify the save directory of the testing `.tsv` files as to not confuse them with the training files by running 
```
python src/oms_sensemaking/nlp/training_data_processor.py --annotated-filepath <path-to-jsonl-file> --save-directory <path-to-save-directory>
```

## Follow these steps to train and test a custom CoreNLP NER model
1. To train a custom CoreNLP NER model, after generating `.tsv` files, the first thing you should do is update [ner.prop], which specifies the path to your training `.tsv` files with the `trainFileList` variable (comma-separated with no spaces). You can change it to use as few or as many `.tsv` files for training as needed.
2. Next, update the location you want to save your custom model to by modifying `serializeTo`.
3. Finally, run `java edu.stanford.nlp.ie.crf.CRFClassifier -prop src/oms_sensemaking/nlp/training/ner.prop`. This will generate a `.ser.gz` file that contains your trained model at the location specified by `serializeTo`. 
4. To test your custom CoreNLP NER model, run `java edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier <path-to-model>.ser.gz -testFile <path-to-test-file>.tsv`. The output should show results that look like [these](https://tex.gerbil-cloud.ts.net:3000/oms/oms-bridge/src/branch/feature/sensemaking-exploration/omsb-sensemaker/docs/train_custom_model_for_corenlp.md#step-4-test-ner-model)

[ner.prop]: ../training/ner.prop