FROM alpine:3.19 AS builder
MAINTAINER Arne Neumann <nlpbox.programming@arne.cl>

RUN apk update && apk add py3-pip wget

WORKDIR /opt

# install grepurl script to retrieve the most current download URL of CoreNLP.
# install latest CoreNLP release.
RUN pip install grepurl --break-system-packages && \
    wget `grepurl -r 'stanford-corenlp-.*\.zip' -a http://stanfordnlp.github.io/CoreNLP` && \
    unzip stanford-corenlp-*.zip && \
    mv $(ls -d stanford-corenlp-*/) corenlp && rm *.zip

# install latest English language model
#
# Docker can't store the result of a RUN command in an ENV, so we'll have
# to use this workaround.
# This command get's the first model file (at least for English there are two)
# and extracts its property file.
WORKDIR /opt/corenlp
RUN wget $(grepurl -r 'english.*jar$' -a http://stanfordnlp.github.io/CoreNLP | head -n 1)


# only keep the things we need to run and test CoreNLP
FROM alpine:3.19

RUN apk update && apk add openjdk8-jre-base py3-pip && \
    pip install pytest pexpect requests --break-system-packages

WORKDIR /opt/corenlp
COPY --from=builder /opt/corenlp .

# Include the custom model(s) --- change to get path from settings
COPY src/oms_sensemaking/nlp/training/ner-model.ser.gz .
COPY src/oms_sensemaking/nlp/training/relation-model.ser.gz .

ENV JAVA_XMX 4g
ENV ANNOTATORS tokenize,ssplit,pos,lemma,ner,depparse,coref,natlog,openie,parse,relation
ENV TIMEOUT_MILLISECONDS 15000

ENV PORT 9000

EXPOSE $PORT


CMD java -Xmx$JAVA_XMX -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -annotators "$ANNOTATORS" -port $PORT -timeout $TIMEOUT_MILLISECONDS
