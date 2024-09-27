from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation
from oms_sensemaking.nlp.models.doccano_result import DoccanoResult
from oms_sensemaking.nlp.training_data_processor import TrainingDataProcessor


def test_process_doccano_result():
    """Tests when entities and relations exist."""
    # Make a test DoccanoEntity
    label = "Thing"
    start_offset_1, end_offset_1 = 34, 41
    start_offset_2, end_offset_2 = 45, 52
    entity_id_1 = 1
    entity_id_2 = 2
    test_ent_1 = DoccanoEntity(id=entity_id_1, label=label, start_offset=start_offset_1, end_offset=end_offset_1)
    test_ent_2 = DoccanoEntity(id=entity_id_2, label=label, start_offset=start_offset_2, end_offset=end_offset_2)

    # Make a test DoccanoRelation
    relation_type = "related_to"
    test_relation = DoccanoRelation(id=11, from_id=entity_id_1, to_id=entity_id_2, type=relation_type)

    # Make a test DoccanoResult
    result_id = 111
    text = "This is some sample text relating Entity1 to Entity2."
    entities = {test_ent_1, test_ent_2}
    relations = {test_relation}
    comments = []
    test_doccano_result = DoccanoResult(result_id, text, entities, relations, comments)

    # Run the function
    tdp = TrainingDataProcessor(annotated_filepath="", save_directory="")
    test_processed_result = tdp.process_doccano_result(test_doccano_result)
    relations = [relation for relation in test_processed_result.processed_relation_set]

    # Assert the output ProcessedResult is correct
    assert test_processed_result.doc_id == result_id
    assert test_processed_result.doc_token_map.get(start_offset_1).token == "Entity1"
    assert test_processed_result.doc_token_map.get(start_offset_2).token == "Entity2"
    assert relations[0].relation_type == relation_type
    assert relations[0].from_token_index == test_processed_result.doc_token_map.get(start_offset_1).index
    assert relations[0].to_token_index == test_processed_result.doc_token_map.get(start_offset_2).index
    assert len(test_processed_result.entity_token_ref) == 2  # Two because there are two entities listed
    assert len(test_processed_result.doc_token_map) == 10  # Ten because there are ten tokens in the provided sentence


def test_process_doccano_result_no_relation():
    """Tests when there are no relations."""
    # Make a test DoccanoEntity
    label = "Thing"
    start_offset_1, end_offset_1 = 34, 41
    start_offset_2, end_offset_2 = 45, 52
    entity_id_1 = 1
    entity_id_2 = 2
    test_ent_1 = DoccanoEntity(id=entity_id_1, label=label, start_offset=start_offset_1, end_offset=end_offset_1)
    test_ent_2 = DoccanoEntity(id=entity_id_2, label=label, start_offset=start_offset_2, end_offset=end_offset_2)

    # Make a test DoccanoResult
    result_id = 111
    text = "This is some sample text relating Entity1 to Entity2."
    entities = {test_ent_1, test_ent_2}
    relations = {}
    comments = []
    test_doccano_result = DoccanoResult(result_id, text, entities, relations, comments)

    # Run the function
    tdp = TrainingDataProcessor(annotated_filepath="", save_directory="")
    test_processed_result = tdp.process_doccano_result(test_doccano_result)
    relations = [relation for relation in test_processed_result.processed_relation_set]

    # Assert the output ProcessedResult is correct
    assert test_processed_result.doc_id == result_id
    assert test_processed_result.doc_token_map.get(start_offset_1).token == "Entity1"
    assert test_processed_result.doc_token_map.get(start_offset_2).token == "Entity2"
    assert len(test_processed_result.entity_token_ref) == 2
    assert len(test_processed_result.doc_token_map) == 10
    assert not relations


def test_process_doccano_result_no_entities_relations():
    """Tests when entities and relations do not exist."""
    # Make a test DoccanoResult
    result_id = 111
    text = "This is some sample text relating Entity1 to Entity2."
    entities = {}
    relations = {}
    comments = []
    test_doccano_result = DoccanoResult(result_id, text, entities, relations, comments)

    # Run the function
    tdp = TrainingDataProcessor(annotated_filepath="", save_directory="")
    test_processed_result = tdp.process_doccano_result(test_doccano_result)
    relations = [relation for relation in test_processed_result.processed_relation_set]

    # Assert the output ProcessedResult is correct
    assert test_processed_result.doc_id == result_id
    assert test_processed_result.entity_token_ref == {}
    assert len(test_processed_result.doc_token_map) == 10
    assert not test_processed_result.entity_token_ref
    assert not relations


def test_tokenize_text():
    """Tests different cases of text to tokenize."""
    tdp = TrainingDataProcessor(annotated_filepath="", save_directory="")

    text1 = "This is some sample text relating Entity1 to Entity2."
    text2 = ""
    text3 = None
    text4 = "ThisissomesampletextrelatingEntity1toEntity2."

    tokenized1 = tdp.tokenize_text(text1)
    tokenized2 = tdp.tokenize_text(text2)
    tokenized3 = tdp.tokenize_text(text3)
    tokenized4 = tdp.tokenize_text(text4)

    assert len(tokenized1) == 10
    assert len(tokenized2) == 0
    assert len(tokenized3) == 0
    assert len(tokenized4) == 2


def test_map_entities_to_tokens():
    """Tests building the mappings between entities and text tokens."""
    # Make a test DoccanoEntity
    label = "Thing"
    start_offset_1, end_offset_1 = 34, 41
    start_offset_2, end_offset_2 = 45, 52
    entity_id_1 = 1
    entity_id_2 = 2
    test_ent_1 = DoccanoEntity(id=entity_id_1, label=label, start_offset=start_offset_1, end_offset=end_offset_1)
    test_ent_2 = DoccanoEntity(id=entity_id_2, label=label, start_offset=start_offset_2, end_offset=end_offset_2)

    # Make a test DoccanoRelation
    relation_type = "related_to"
    test_relation = DoccanoRelation(id=11, from_id=entity_id_1, to_id=entity_id_2, type=relation_type)

    # Make a test DoccanoResult
    result_id = 111
    text = "This is some sample text relating Entity1 to Entity2."
    entities = {test_ent_1, test_ent_2}
    relations = {test_relation}
    comments = []
    test_doccano_result = DoccanoResult(result_id, text, entities, relations, comments)

    # Run the function
    tdp = TrainingDataProcessor(annotated_filepath="", save_directory="")
    # test_processed_result = tdp.process_doccano_result(test_doccano_result)
    tokenized_text_map = tdp.tokenize_text(text)
    mapped_entities = tdp.map_entities_to_tokens(test_doccano_result, tokenized_text_map)

    assert len(mapped_entities) == 2
    assert mapped_entities[1].token == "Entity1"
    assert mapped_entities[2].token == "Entity2"
