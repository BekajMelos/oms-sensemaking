"""Utilities for installing CoreNLP."""
import stanza

# Must run this file via `python src/oms_sensemaking/nlp/install_corenlp_client.py` prior to
# using any files that require CoreNLP. This installs CoreNLP source files onto your local machine.
stanza.install_corenlp()
