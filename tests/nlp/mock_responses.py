"""Mock responses for NLP testing using the MockCoreNlpClient"""

mock_response_long_text_xml = [
    {
        "@id": "1",
        "tokens": {
            "token": [
                {
                    "@id": "1",
                    "word": "EU",
                    "lemma": "EU",
                    "CharacterOffsetBegin": "0",
                    "CharacterOffsetEnd": "2",
                    "POS": "NNP",
                    "NER": "ORGANIZATION",
                },
                {
                    "@id": "2",
                    "word": "rejects",
                    "lemma": "reject",
                    "CharacterOffsetBegin": "3",
                    "CharacterOffsetEnd": "10",
                    "POS": "VBZ",
                    "NER": "O",
                },
                {
                    "@id": "3",
                    "word": "German",
                    "lemma": "German",
                    "CharacterOffsetBegin": "11",
                    "CharacterOffsetEnd": "17",
                    "POS": "JJ",
                    "NER": "NATIONALITY",
                },
                {
                    "@id": "4",
                    "word": "call",
                    "lemma": "call",
                    "CharacterOffsetBegin": "18",
                    "CharacterOffsetEnd": "22",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "5",
                    "word": "to",
                    "lemma": "to",
                    "CharacterOffsetBegin": "23",
                    "CharacterOffsetEnd": "25",
                    "POS": "TO",
                    "NER": "O",
                },
                {
                    "@id": "6",
                    "word": "boycott",
                    "lemma": "boycott",
                    "CharacterOffsetBegin": "26",
                    "CharacterOffsetEnd": "33",
                    "POS": "VB",
                    "NER": "O",
                },
                {
                    "@id": "7",
                    "word": "British",
                    "lemma": "British",
                    "CharacterOffsetBegin": "34",
                    "CharacterOffsetEnd": "41",
                    "POS": "JJ",
                    "NER": "NATIONALITY",
                },
                {
                    "@id": "8",
                    "word": "lamb",
                    "lemma": "lamb",
                    "CharacterOffsetBegin": "42",
                    "CharacterOffsetEnd": "46",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "9",
                    "word": ".",
                    "lemma": ".",
                    "CharacterOffsetBegin": "46",
                    "CharacterOffsetEnd": "47",
                    "POS": ".",
                    "NER": "O",
                },
            ]
        },
        "parse": "(ROOT (S (NP (NNP EU)) (VP (VBZ rejects) (NP (JJ German) (NN call)) (S (VP (TO to) (VP (VB boycott) "
        "(NP (JJ British) (NN lamb)))))) (. .)))",
        "dependencies": [
            {
                "@type": "basic-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "2", "#text": "rejects"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "1", "#text": "EU"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "call"},
                        "dependent": {"@idx": "3", "#text": "German"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "4", "#text": "call"},
                    },
                    {
                        "@type": "mark",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "5", "#text": "to"},
                    },
                    {
                        "@type": "advcl",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "6", "#text": "boycott"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "8", "#text": "lamb"},
                        "dependent": {"@idx": "7", "#text": "British"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "8", "#text": "lamb"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "9", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "2", "#text": "rejects"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "1", "#text": "EU"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "call"},
                        "dependent": {"@idx": "3", "#text": "German"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "4", "#text": "call"},
                    },
                    {
                        "@type": "mark",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "5", "#text": "to"},
                    },
                    {
                        "@type": "advcl",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "6", "#text": "boycott"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "8", "#text": "lamb"},
                        "dependent": {"@idx": "7", "#text": "British"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "8", "#text": "lamb"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "9", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-ccprocessed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "2", "#text": "rejects"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "1", "#text": "EU"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "call"},
                        "dependent": {"@idx": "3", "#text": "German"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "4", "#text": "call"},
                    },
                    {
                        "@type": "mark",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "5", "#text": "to"},
                    },
                    {
                        "@type": "advcl",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "6", "#text": "boycott"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "8", "#text": "lamb"},
                        "dependent": {"@idx": "7", "#text": "British"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "8", "#text": "lamb"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "9", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "2", "#text": "rejects"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "1", "#text": "EU"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "call"},
                        "dependent": {"@idx": "3", "#text": "German"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "4", "#text": "call"},
                    },
                    {
                        "@type": "mark",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "5", "#text": "to"},
                    },
                    {
                        "@type": "advcl:to",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "6", "#text": "boycott"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "8", "#text": "lamb"},
                        "dependent": {"@idx": "7", "#text": "British"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "8", "#text": "lamb"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "9", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-plus-plus-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "2", "#text": "rejects"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "1", "#text": "EU"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "call"},
                        "dependent": {"@idx": "3", "#text": "German"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "4", "#text": "call"},
                    },
                    {
                        "@type": "mark",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "5", "#text": "to"},
                    },
                    {
                        "@type": "advcl:to",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "6", "#text": "boycott"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "8", "#text": "lamb"},
                        "dependent": {"@idx": "7", "#text": "British"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "boycott"},
                        "dependent": {"@idx": "8", "#text": "lamb"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "2", "#text": "rejects"},
                        "dependent": {"@idx": "9", "#text": "."},
                    },
                ],
            },
        ],
        "MachineReading": {
            "entities": {
                "entity": [
                    {
                        "@id": "EntityMention-69",
                        "span": {"@start": "0", "@end": "1"},
                        "probabilities": None,
                        "#text": "ORGANIZATION",
                    },
                    {
                        "@id": "EntityMention-70",
                        "span": {"@start": "2", "@end": "3"},
                        "probabilities": None,
                        "#text": "O",
                    },
                    {
                        "@id": "EntityMention-71",
                        "span": {"@start": "6", "@end": "7"},
                        "probabilities": None,
                        "#text": "O",
                    },
                ]
            },
            "relations": {
                "relation": [
                    {
                        "@id": "RelationMention-381",
                        "arguments": {
                            "entity": [
                                {
                                    "@id": "EntityMention-75",
                                    "span": {"@start": "1", "@end": "2"},
                                    "probabilities": None,
                                    "#text": "PEOPLE",
                                },
                                {
                                    "@id": "EntityMention-76",
                                    "span": {"@start": "2", "@end": "3"},
                                    "probabilities": None,
                                    "#text": "O",
                                },
                            ]
                        },
                        "probabilities": {
                            "probability": [
                                {"label": "OrgBased_In", "value": "0.48585554167441475"},
                                {"label": "_NR", "value": "0.39204863807261303"},
                                {"label": "Work_For", "value": "0.05697886976897943"},
                                {"label": "Live_In", "value": "0.040949749969748574"},
                                {"label": "Located_In", "value": "0.02416720051424407"},
                            ]
                        },
                        "#text": "OrgBased_In",
                    }
                ]
            },
        },
    }
]
mock_response_normal_text_xml = [
    {
        "@id": "1",
        "tokens": {
            "token": [
                {
                    "@id": "1",
                    "word": "This",
                    "lemma": "this",
                    "CharacterOffsetBegin": "0",
                    "CharacterOffsetEnd": "4",
                    "POS": "DT",
                    "NER": "O",
                },
                {
                    "@id": "2",
                    "word": "is",
                    "lemma": "be",
                    "CharacterOffsetBegin": "5",
                    "CharacterOffsetEnd": "7",
                    "POS": "VBZ",
                    "NER": "O",
                },
                {
                    "@id": "3",
                    "word": "some",
                    "lemma": "some",
                    "CharacterOffsetBegin": "8",
                    "CharacterOffsetEnd": "12",
                    "POS": "DT",
                    "NER": "O",
                },
                {
                    "@id": "4",
                    "word": "sample",
                    "lemma": "sample",
                    "CharacterOffsetBegin": "13",
                    "CharacterOffsetEnd": "19",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "5",
                    "word": "text",
                    "lemma": "text",
                    "CharacterOffsetBegin": "20",
                    "CharacterOffsetEnd": "24",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "6",
                    "word": "relating",
                    "lemma": "relate",
                    "CharacterOffsetBegin": "25",
                    "CharacterOffsetEnd": "33",
                    "POS": "VBG",
                    "NER": "O",
                },
                {
                    "@id": "7",
                    "word": "Entity1",
                    "lemma": "entity1",
                    "CharacterOffsetBegin": "34",
                    "CharacterOffsetEnd": "41",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "8",
                    "word": "to",
                    "lemma": "to",
                    "CharacterOffsetBegin": "42",
                    "CharacterOffsetEnd": "44",
                    "POS": "IN",
                    "NER": "O",
                },
                {
                    "@id": "9",
                    "word": "Entity2",
                    "lemma": "entity2",
                    "CharacterOffsetBegin": "45",
                    "CharacterOffsetEnd": "52",
                    "POS": "NN",
                    "NER": "O",
                },
                {
                    "@id": "10",
                    "word": ".",
                    "lemma": ".",
                    "CharacterOffsetBegin": "52",
                    "CharacterOffsetEnd": "53",
                    "POS": ".",
                    "NER": "O",
                },
            ]
        },
        "parse": "(ROOT (S (NP (DT This)) (VP (VBZ is) (NP (NP (DT some) (NN sample) (NN text)) (VP (VBG relating) ("
        "NP (NN Entity1)) (PP (IN to) (NP (NN Entity2)))))) (. .)))",
        "dependencies": [
            {
                "@type": "basic-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "text"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "1", "#text": "This"},
                    },
                    {
                        "@type": "cop",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "2", "#text": "is"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "3", "#text": "some"},
                    },
                    {
                        "@type": "compound",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "4", "#text": "sample"},
                    },
                    {
                        "@type": "acl",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "6", "#text": "relating"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "7", "#text": "Entity1"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "Entity2"},
                        "dependent": {"@idx": "8", "#text": "to"},
                    },
                    {
                        "@type": "obl",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "9", "#text": "Entity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "text"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "1", "#text": "This"},
                    },
                    {
                        "@type": "cop",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "2", "#text": "is"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "3", "#text": "some"},
                    },
                    {
                        "@type": "compound",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "4", "#text": "sample"},
                    },
                    {
                        "@type": "acl",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "6", "#text": "relating"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "7", "#text": "Entity1"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "Entity2"},
                        "dependent": {"@idx": "8", "#text": "to"},
                    },
                    {
                        "@type": "obl:to",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "9", "#text": "Entity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-ccprocessed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "text"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "1", "#text": "This"},
                    },
                    {
                        "@type": "cop",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "2", "#text": "is"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "3", "#text": "some"},
                    },
                    {
                        "@type": "compound",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "4", "#text": "sample"},
                    },
                    {
                        "@type": "acl",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "6", "#text": "relating"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "7", "#text": "Entity1"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "Entity2"},
                        "dependent": {"@idx": "8", "#text": "to"},
                    },
                    {
                        "@type": "obl:to",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "9", "#text": "Entity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "text"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "1", "#text": "This"},
                    },
                    {
                        "@type": "cop",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "2", "#text": "is"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "3", "#text": "some"},
                    },
                    {
                        "@type": "compound",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "4", "#text": "sample"},
                    },
                    {
                        "@type": "acl",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "6", "#text": "relating"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "7", "#text": "Entity1"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "Entity2"},
                        "dependent": {"@idx": "8", "#text": "to"},
                    },
                    {
                        "@type": "obl:to",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "9", "#text": "Entity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-plus-plus-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "text"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "1", "#text": "This"},
                    },
                    {
                        "@type": "cop",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "2", "#text": "is"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "3", "#text": "some"},
                    },
                    {
                        "@type": "compound",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "4", "#text": "sample"},
                    },
                    {
                        "@type": "acl",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "6", "#text": "relating"},
                    },
                    {
                        "@type": "obj",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "7", "#text": "Entity1"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "Entity2"},
                        "dependent": {"@idx": "8", "#text": "to"},
                    },
                    {
                        "@type": "obl:to",
                        "governor": {"@idx": "6", "#text": "relating"},
                        "dependent": {"@idx": "9", "#text": "Entity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "text"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
        ],
    }
]
mock_response_short_text_xml = [
    {
        "@id": "1",
        "tokens": {
            "token": [
                {
                    "@id": "1",
                    "word": "The",
                    "lemma": "the",
                    "CharacterOffsetBegin": "0",
                    "CharacterOffsetEnd": "3",
                    "POS": "DT",
                },
                {
                    "@id": "2",
                    "word": "quick",
                    "lemma": "quick",
                    "CharacterOffsetBegin": "4",
                    "CharacterOffsetEnd": "9",
                    "POS": "JJ",
                },
                {
                    "@id": "3",
                    "word": "brown",
                    "lemma": "brown",
                    "CharacterOffsetBegin": "10",
                    "CharacterOffsetEnd": "15",
                    "POS": "JJ",
                },
                {
                    "@id": "4",
                    "word": "fox",
                    "lemma": "fox",
                    "CharacterOffsetBegin": "16",
                    "CharacterOffsetEnd": "19",
                    "POS": "NN",
                },
                {
                    "@id": "5",
                    "word": "jumps",
                    "lemma": "jump",
                    "CharacterOffsetBegin": "20",
                    "CharacterOffsetEnd": "25",
                    "POS": "VBZ",
                },
                {
                    "@id": "6",
                    "word": "over",
                    "lemma": "over",
                    "CharacterOffsetBegin": "26",
                    "CharacterOffsetEnd": "30",
                    "POS": "IN",
                },
                {
                    "@id": "7",
                    "word": "the",
                    "lemma": "the",
                    "CharacterOffsetBegin": "31",
                    "CharacterOffsetEnd": "34",
                    "POS": "DT",
                },
                {
                    "@id": "8",
                    "word": "lazy",
                    "lemma": "lazy",
                    "CharacterOffsetBegin": "35",
                    "CharacterOffsetEnd": "39",
                    "POS": "JJ",
                },
                {
                    "@id": "9",
                    "word": "dog",
                    "lemma": "dog",
                    "CharacterOffsetBegin": "40",
                    "CharacterOffsetEnd": "43",
                    "POS": "NN",
                },
                {
                    "@id": "10",
                    "word": ".",
                    "lemma": ".",
                    "CharacterOffsetBegin": "43",
                    "CharacterOffsetEnd": "44",
                    "POS": ".",
                },
            ]
        },
        "dependencies": [
            {
                "@type": "basic-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "jumps"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "1", "#text": "The"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "2", "#text": "quick"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "3", "#text": "brown"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "4", "#text": "fox"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "6", "#text": "over"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "7", "#text": "the"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "8", "#text": "lazy"},
                    },
                    {
                        "@type": "obl",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "9", "#text": "dog"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "jumps"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "1", "#text": "The"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "2", "#text": "quick"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "3", "#text": "brown"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "4", "#text": "fox"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "6", "#text": "over"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "7", "#text": "the"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "8", "#text": "lazy"},
                    },
                    {
                        "@type": "obl:over",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "9", "#text": "dog"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-ccprocessed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "jumps"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "1", "#text": "The"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "2", "#text": "quick"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "3", "#text": "brown"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "4", "#text": "fox"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "6", "#text": "over"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "7", "#text": "the"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "8", "#text": "lazy"},
                    },
                    {
                        "@type": "obl:over",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "9", "#text": "dog"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "jumps"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "1", "#text": "The"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "2", "#text": "quick"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "3", "#text": "brown"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "4", "#text": "fox"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "6", "#text": "over"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "7", "#text": "the"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "8", "#text": "lazy"},
                    },
                    {
                        "@type": "obl:over",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "9", "#text": "dog"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-plus-plus-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "5", "#text": "jumps"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "1", "#text": "The"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "2", "#text": "quick"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "4", "#text": "fox"},
                        "dependent": {"@idx": "3", "#text": "brown"},
                    },
                    {
                        "@type": "nsubj",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "4", "#text": "fox"},
                    },
                    {
                        "@type": "case",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "6", "#text": "over"},
                    },
                    {
                        "@type": "det",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "7", "#text": "the"},
                    },
                    {
                        "@type": "amod",
                        "governor": {"@idx": "9", "#text": "dog"},
                        "dependent": {"@idx": "8", "#text": "lazy"},
                    },
                    {
                        "@type": "obl:over",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "9", "#text": "dog"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "5", "#text": "jumps"},
                        "dependent": {"@idx": "10", "#text": "."},
                    },
                ],
            },
        ],
    }
]
mock_response_bunched_text_xml = [
    {
        "@id": "1",
        "tokens": {
            "token": [
                {
                    "@id": "1",
                    "word": "ThisissomesampletextrelatingEntity1toEntity2",
                    "lemma": "thisissomesampletextrelatingentity1toentity2",
                    "CharacterOffsetBegin": "0",
                    "CharacterOffsetEnd": "44",
                    "POS": "NN",
                },
                {
                    "@id": "2",
                    "word": ".",
                    "lemma": ".",
                    "CharacterOffsetBegin": "44",
                    "CharacterOffsetEnd": "45",
                    "POS": ".",
                },
            ]
        },
        "dependencies": [
            {
                "@type": "basic-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                        "dependent": {"@idx": "2", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                        "dependent": {"@idx": "2", "#text": "."},
                    },
                ],
            },
            {
                "@type": "collapsed-ccprocessed-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                        "dependent": {"@idx": "2", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                        "dependent": {"@idx": "2", "#text": "."},
                    },
                ],
            },
            {
                "@type": "enhanced-plus-plus-dependencies",
                "dep": [
                    {
                        "@type": "root",
                        "governor": {"@idx": "0", "#text": "ROOT"},
                        "dependent": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                    },
                    {
                        "@type": "punct",
                        "governor": {"@idx": "1", "#text": "ThisissomesampletextrelatingEntity1toEntity2"},
                        "dependent": {"@idx": "2", "#text": "."},
                    },
                ],
            },
        ],
    }
]
mock_response_no_text_xml = []
mock_response_long_text_str = """Sentence #3 (41 tokens):
The commander of the 21st Battalion, who goes by the call sign Kucher, said that when his men arrived in the Krasnohorivka area in the spring, they had roughly the same number of men as the Russians.

Tokens:
[Text=The CharacterOffsetBegin=175 CharacterOffsetEnd=178 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=commander CharacterOffsetBegin=179 CharacterOffsetEnd=188 PartOfSpeech=NN Lemma=commander NamedEntityTag=Job]
[Text=of CharacterOffsetBegin=189 CharacterOffsetEnd=191 PartOfSpeech=IN Lemma=of NamedEntityTag=0]
[Text=the CharacterOffsetBegin=192 CharacterOffsetEnd=195 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=21st CharacterOffsetBegin=196 CharacterOffsetEnd=200 PartOfSpeech=NNP Lemma=21st NamedEntityTag=B-Organization]
[Text=Battalion CharacterOffsetBegin=201 CharacterOffsetEnd=210 PartOfSpeech=NNP Lemma=Battalion NamedEntityTag=E-Organization]
[Text=, CharacterOffsetBegin=210 CharacterOffsetEnd=211 PartOfSpeech=, Lemma=, NamedEntityTag=0]
[Text=who CharacterOffsetBegin=212 CharacterOffsetEnd=215 PartOfSpeech=WP Lemma=who NamedEntityTag=0]
[Text=goes CharacterOffsetBegin=216 CharacterOffsetEnd=220 PartOfSpeech=VBZ Lemma=go NamedEntityTag=0]
[Text=by CharacterOffsetBegin=221 CharacterOffsetEnd=223 PartOfSpeech=IN Lemma=by NamedEntityTag=0]
[Text=the CharacterOffsetBegin=224 CharacterOffsetEnd=227 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=call CharacterOffsetBegin=228 CharacterOffsetEnd=232 PartOfSpeech=NN Lemma=call NamedEntityTag=0]
[Text=sign CharacterOffsetBegin=233 CharacterOffsetEnd=237 PartOfSpeech=NN Lemma=sign NamedEntityTag=0]
[Text=Kucher CharacterOffsetBegin=238 CharacterOffsetEnd=244 PartOfSpeech=NNP Lemma=Kucher NamedEntityTag=Person]
[Text=, CharacterOffsetBegin=244 CharacterOffsetEnd=245 PartOfSpeech=, Lemma=, NamedEntityTag=0]
[Text=said CharacterOffsetBegin=246 CharacterOffsetEnd=250 PartOfSpeech=VBD Lemma=say NamedEntityTag=0]
[Text=that CharacterOffsetBegin=251 CharacterOffsetEnd=255 PartOfSpeech=IN Lemma=that NamedEntityTag=0]
[Text=when CharacterOffsetBegin=256 CharacterOffsetEnd=260 PartOfSpeech=WRB Lemma=when NamedEntityTag=0]
[Text=his CharacterOffsetBegin=261 CharacterOffsetEnd=264 PartOfSpeech=PRP$ Lemma=he NamedEntityTag=0]
[Text=men CharacterOffsetBegin=265 CharacterOffsetEnd=268 PartOfSpeech=NNS Lemma=man NamedEntityTag=0]
[Text=arrived CharacterOffsetBegin=269 CharacterOffsetEnd=276 PartOfSpeech=VBD Lemma=arrive NamedEntityTag=0]
[Text=in CharacterOffsetBegin=277 CharacterOffsetEnd=279 PartOfSpeech=IN Lemma=in NamedEntityTag=0]
[Text=the CharacterOffsetBegin=280 CharacterOffsetEnd=283 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=Krasnohorivka CharacterOffsetBegin=284 CharacterOffsetEnd=297 PartOfSpeech=NNP Lemma=Krasnohorivka NamedEntityTag=Location]
[Text=area CharacterOffsetBegin=298 CharacterOffsetEnd=302 PartOfSpeech=NN Lemma=area NamedEntityTag=0]
[Text=in CharacterOffsetBegin=303 CharacterOffsetEnd=305 PartOfSpeech=IN Lemma=in NamedEntityTag=0]
[Text=the CharacterOffsetBegin=306 CharacterOffsetEnd=309 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=spring CharacterOffsetBegin=310 CharacterOffsetEnd=316 PartOfSpeech=NN Lemma=spring NamedEntityTag=0 Timex=<TIMEX3 tid="t1" type="DATE" value="XXXX-SP">spring</TIMEX3>]
[Text=, CharacterOffsetBegin=316 CharacterOffsetEnd=317 PartOfSpeech=, Lemma=, NamedEntityTag=0]
[Text=they CharacterOffsetBegin=318 CharacterOffsetEnd=322 PartOfSpeech=PRP Lemma=they NamedEntityTag=0]
[Text=had CharacterOffsetBegin=323 CharacterOffsetEnd=326 PartOfSpeech=VBD Lemma=have NamedEntityTag=0]
[Text=roughly CharacterOffsetBegin=327 CharacterOffsetEnd=334 PartOfSpeech=RB Lemma=roughly NamedEntityTag=0]
[Text=the CharacterOffsetBegin=335 CharacterOffsetEnd=338 PartOfSpeech=DT Lemma=the NamedEntityTag=0]
[Text=same CharacterOffsetBegin=339 CharacterOffsetEnd=343 PartOfSpeech=JJ Lemma=same NamedEntityTag=0]
[Text=number CharacterOffsetBegin=344 CharacterOffsetEnd=350 PartOfSpeech=NN Lemma=number NamedEntityTag=0]
[Text=of CharacterOffsetBegin=351 CharacterOffsetEnd=353 PartOfSpeech=IN Lemma=of NamedEntityTag=0]
[Text=men CharacterOffsetBegin=354 CharacterOffsetEnd=357 PartOfSpeech=NNS Lemma=man NamedEntityTag=0]
[Text=as CharacterOffsetBegin=358 CharacterOffsetEnd=360 PartOfSpeech=IN Lemma=as NamedEntityTag=0]
[Text=the CharacterOffsetBegin=361 CharacterOffsetEnd=364 PartOfSpeech=DT Lemma=the NamedEntityTag=B-Organization]
[Text=Russians CharacterOffsetBegin=365 CharacterOffsetEnd=373 PartOfSpeech=NNPS Lemma=Russian NamedEntityTag=E-Organization]
[Text=. CharacterOffsetBegin=373 CharacterOffsetEnd=374 PartOfSpeech=. Lemma=. NamedEntityTag=0]


Extracted the following MachineReading entity mentions:
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-32, hstart=4, hend=5, estart=4, eend=5, headPosition=4, value="21st", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]

Extracted the following MachineReading relation mentions:
RelationMention [type=Has_Job, start=0, end=4, {Has_Job, 0.36154404689274855; _NR, 0.22665045564315542; Part_of_Org, 0.21548344761984883; Located_In, 0.19632204984424717}
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
]
RelationMention [type=Part_of_Org, start=0, end=6, {Part_of_Org, 0.3799914414560246; Has_Job, 0.21920034690594214; _NR, 0.20656761833540274; Located_In, 0.19424059330263027}
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=0, end=24, {Located_In, 0.6069519736360233; Has_Job, 0.16337295174431699; Part_of_Org, 0.1589464119862941; _NR, 0.07072866263336577}
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Part_of_Org, start=1, end=6, {Part_of_Org, 0.37229120555246503; _NR, 0.23462838715156478; Has_Job, 0.2115729222746853; Located_In, 0.18150748502128491}
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=14, {Has_Job, 0.4701741809228693; Part_of_Org, 0.20811700748893114; Located_In, 0.19427134278999936; _NR, 0.12743746879819992}
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
]
RelationMention [type=Located_In, start=1, end=24, {Located_In, 0.5934876165816858; Has_Job, 0.1658604263931852; Part_of_Org, 0.16148689411121445; _NR, 0.07916506291391467}
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=0, end=4, {Has_Job, 0.3608835360396095; _NR, 0.22876902093976437; Part_of_Org, 0.21553861872578356; Located_In, 0.1948088242948426}
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
]
RelationMention [type=Part_of_Org, start=2, end=6, {Part_of_Org, 0.3674430654608884; _NR, 0.24130012732092648; Has_Job, 0.21098875160665248; Located_In, 0.18026805561153258}
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=2, end=24, {Located_In, 0.5867518518896805; Has_Job, 0.16475936053165227; Part_of_Org, 0.16121908031849436; _NR, 0.08726970726017277}
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=5, {Has_Job, 0.415069819321793; _NR, 0.21105869619902204; Part_of_Org, 0.2003056957049721; Located_In, 0.17356578877421278}
    EntityMention [type=O, objectId=EntityMention-32, hstart=4, hend=5, estart=4, eend=5, headPosition=4, value="21st", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Located_In, start=4, end=24, {Located_In, 0.5760596856761706; Has_Job, 0.16910784481119506; Part_of_Org, 0.1601224805532249; _NR, 0.09470998895940941}
    EntityMention [type=O, objectId=EntityMention-32, hstart=4, hend=5, estart=4, eend=5, headPosition=4, value="21st", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Part_of_Org, start=0, end=6, {Part_of_Org, 0.3419742127670538; Located_In, 0.30263596193685904; Has_Job, 0.2068526860382915; _NR, 0.14853713925779571}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=6, {Has_Job, 0.36284273393077926; Part_of_Org, 0.3014265429208627; Located_In, 0.2418394205682765; _NR, 0.09389130258008162}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=2, end=6, {Part_of_Org, 0.3356580173694437; Located_In, 0.2875319641940447; Has_Job, 0.20252772064767374; _NR, 0.1742822977888378}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=13, {Part_of_Org, 0.34310492257513137; Located_In, 0.29536174222857103; Has_Job, 0.2043918180801398; _NR, 0.15714151711615781}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=14, {Part_of_Org, 0.5233358645237898; Located_In, 0.23298211058850374; Has_Job, 0.17040154653300077; _NR, 0.07328047835470589}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=23, {Part_of_Org, 0.34447923706507594; Located_In, 0.30370897429988314; Has_Job, 0.2077056105407745; _NR, 0.14410617809426657}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
]
RelationMention [type=Located_In, start=5, end=24, {Located_In, 0.8447979577892142; Part_of_Org, 0.0910634811110897; Has_Job, 0.0580537995205256; _NR, 0.006084761579170508}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=38, {Part_of_Org, 0.34511268723697097; Located_In, 0.3039356123340341; Has_Job, 0.2067884216469872; _NR, 0.1441632787820078}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=39, {Part_of_Org, 0.32619081591617827; Located_In, 0.2696080220100633; _NR, 0.20875321388844006; Has_Job, 0.19544794818531844}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=40, {Part_of_Org, 0.33775578940967055; Located_In, 0.2901631474576658; Has_Job, 0.20398881429848878; _NR, 0.16809224883417492}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=41, {Part_of_Org, 0.33159639468659957; Located_In, 0.28999333694148277; Has_Job, 0.20044753455257774; _NR, 0.17796273381933975}
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=13, {Has_Job, 0.4320441711366447; Part_of_Org, 0.2121977066903143; Located_In, 0.19077239231865448; _NR, 0.16498572985438661}
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=13, {Part_of_Org, 0.3802401362463741; Has_Job, 0.21720650074743353; _NR, 0.2127616022128915; Located_In, 0.18979176079330085}
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=6, end=24, {Located_In, 0.6030082910548004; Has_Job, 0.1634797855710171; Part_of_Org, 0.16061022583379742; _NR, 0.07290169754038535}
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=0, end=14, {Has_Job, 0.40265776468772385; Part_of_Org, 0.3528938579278767; Located_In, 0.16827087785491746; _NR, 0.07617749952948195}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=14, {Has_Job, 0.8891218226781434; Part_of_Org, 0.07565199435107495; Located_In, 0.03300972054494595; _NR, 0.0022164624258356243}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Has_Job, start=2, end=14, {Has_Job, 0.3981962813641644; Part_of_Org, 0.35017291879627993; Located_In, 0.161779088972084; _NR, 0.08985171086747168}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
]
RelationMention [type=Has_Job, start=4, end=14, {Has_Job, 0.40427074145762776; Part_of_Org, 0.34412626228231613; Located_In, 0.15846568757862037; _NR, 0.09313730868143574}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-32, hstart=4, hend=5, estart=4, eend=5, headPosition=4, value="21st", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=14, {Part_of_Org, 0.7960632989509436; Has_Job, 0.14532856991727322; Located_In, 0.0515127843648015; _NR, 0.007095346766981649}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Has_Job, start=6, end=14, {Has_Job, 0.39878791228920274; Part_of_Org, 0.354763383534473; Located_In, 0.16575012487770613; _NR, 0.08069857929861796}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
]
RelationMention [type=Has_Job, start=13, end=23, {Has_Job, 0.402798092058277; Part_of_Org, 0.3535306616285909; Located_In, 0.16603968545245656; _NR, 0.07763156086067562}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
]
RelationMention [type=Located_In, start=13, end=24, {Located_In, 0.42098361025614073; Has_Job, 0.30099664021119155; Part_of_Org, 0.2528744295462081; _NR, 0.025145319986459705}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=13, end=38, {Has_Job, 0.4012109886392775; Part_of_Org, 0.3550190270269804; Located_In, 0.16819106194092254; _NR, 0.07557892239281963}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
]
RelationMention [type=Has_Job, start=13, end=39, {Has_Job, 0.38986645778699897; Part_of_Org, 0.34517409040879243; Located_In, 0.15379819861240204; _NR, 0.11116125319180659}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
]
RelationMention [type=Has_Job, start=13, end=40, {Has_Job, 0.39942619502075116; Part_of_Org, 0.34984296763545686; Located_In, 0.16177237886563953; _NR, 0.08895845847815245}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
]
RelationMention [type=Has_Job, start=13, end=41, {Has_Job, 0.39537741285908196; Part_of_Org, 0.34683904206630023; Located_In, 0.16316356349931455; _NR, 0.09461998157530313}
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=23, {Has_Job, 0.43587120576243554; Part_of_Org, 0.21274950811687807; Located_In, 0.19248578428987317; _NR, 0.15889350183081324}
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=23, {Part_of_Org, 0.3841999637471324; Has_Job, 0.22076633446889357; _NR, 0.20006439024265227; Located_In, 0.1949693115413218}
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=14, end=24, {Located_In, 0.6059426967979245; Has_Job, 0.16416240718843048; Part_of_Org, 0.1602276646860527; _NR, 0.06966723132759248}
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=24, {Has_Job, 0.42845724536647767; Part_of_Org, 0.209090423655589; _NR, 0.18204255801486693; Located_In, 0.18040977296306637}
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=24, {Part_of_Org, 0.37008063016310433; Located_In, 0.22975388571925043; Has_Job, 0.2157145892096286; _NR, 0.18445089490801664}
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=23, end=40, {Located_In, 0.3406010746288789; Part_of_Org, 0.22373253817684696; Has_Job, 0.2237283706633404; _NR, 0.2119380165309339}
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=38, {Has_Job, 0.43733586504627986; Part_of_Org, 0.21319484776214115; Located_In, 0.19393543519228917; _NR, 0.1555338519992901}
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=38, {Part_of_Org, 0.3855954219584864; Has_Job, 0.22168248789047873; Located_In, 0.19671518788359865; _NR, 0.19600690226743633}
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=23, end=38, {Located_In, 0.49613893498639594; _NR, 0.2159077477762335; Has_Job, 0.14404875557976468; Part_of_Org, 0.1439045616576058}
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=39, {Has_Job, 0.4033567981586286; _NR, 0.22910218111142155; Part_of_Org, 0.1993209952417775; Located_In, 0.16822002548817241}
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=39, {Part_of_Org, 0.3515822198652978; _NR, 0.28094129184545635; Has_Job, 0.20044093913311864; Located_In, 0.16703554915612714}
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=23, end=39, {Located_In, 0.564291506785251; Has_Job, 0.16430230569329174; Part_of_Org, 0.16188261335458654; _NR, 0.10952357416687059}
    EntityMention [type=O, objectId=EntityMention-39, hstart=38, hend=39, estart=38, eend=39, headPosition=38, value="the", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Located_In, start=0, end=40, {Located_In, 0.3095105042352265; _NR, 0.23320086707910298; Has_Job, 0.22869156258759898; Part_of_Org, 0.22859706609807126}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-29, hstart=0, hend=1, estart=0, eend=1, headPosition=0, value="The", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=40, {Has_Job, 0.4135704477050623; Located_In, 0.2519189411289828; Part_of_Org, 0.20136959460089776; _NR, 0.13314101656505717}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Located_In, start=2, end=40, {Located_In, 0.28955253709559386; _NR, 0.2688062580018332; Part_of_Org, 0.22111406027324743; Has_Job, 0.2205271446293254}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-31, hstart=2, hend=3, estart=2, eend=4, headPosition=2, value="of", corefID=-1]
]
RelationMention [type=Located_In, start=4, end=40, {Located_In, 0.2848012225641275; _NR, 0.2741184697305068; Has_Job, 0.22368040311259849; Part_of_Org, 0.21739990459276737}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-32, hstart=4, hend=5, estart=4, eend=5, headPosition=4, value="21st", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=40, {Part_of_Org, 0.3651452364809765; Located_In, 0.2558453705919832; Has_Job, 0.210115847365275; _NR, 0.1688935455617655}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=6, end=40, {Located_In, 0.3028210085618683; _NR, 0.24399623837358098; Part_of_Org, 0.22826801463669677; Has_Job, 0.22491473842785406}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-34, hstart=7, hend=8, estart=6, eend=13, headPosition=7, value="who", corefID=-1]
]
RelationMention [type=Located_In, start=13, end=40, {Located_In, 0.3033093628342295; _NR, 0.24023859144951795; Has_Job, 0.22911400249652625; Part_of_Org, 0.2273380432197262}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=PEOPLE, objectId=EntityMention-35, hstart=13, hend=14, estart=13, eend=14, headPosition=13, value="Kucher", corefID=-1]
]
RelationMention [type=Located_In, start=14, end=40, {Located_In, 0.3095460181656298; _NR, 0.2310044682612845; Part_of_Org, 0.22996094503835668; Has_Job, 0.22948856853472913}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-36, hstart=15, hend=16, estart=14, eend=23, headPosition=15, value="said", corefID=-1]
]
RelationMention [type=Located_In, start=23, end=40, {Located_In, 0.8622192979959353; Has_Job, 0.06488918036092188; Part_of_Org, 0.0632379338892178; _NR, 0.009653587753925172}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
RelationMention [type=Located_In, start=24, end=40, {Located_In, 0.3098584174290385; _NR, 0.2311761224923791; Part_of_Org, 0.23038020382486246; Has_Job, 0.2285852562537199}
    EntityMention [type=O, objectId=EntityMention-40, hstart=39, hend=40, estart=39, eend=40, headPosition=39, value="Russians", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-38, hstart=24, hend=25, estart=24, eend=38, headPosition=24, value="area", corefID=-1]
]
RelationMention [type=Has_Job, start=1, end=41, {Has_Job, 0.41685970038412856; Part_of_Org, 0.2033984422116333; _NR, 0.19775988657249144; Located_In, 0.1819819708317466}
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-30, hstart=1, hend=2, estart=1, eend=2, headPosition=1, value="commander", corefID=-1]
]
RelationMention [type=Part_of_Org, start=5, end=41, {Part_of_Org, 0.3635568903497176; _NR, 0.2445739438604064; Has_Job, 0.20919526870781463; Located_In, 0.18267389708206144}
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]
    EntityMention [type=O, objectId=EntityMention-33, hstart=5, hend=6, estart=5, eend=6, headPosition=5, value="Battalion", corefID=-1]
]
RelationMention [type=Located_In, start=23, end=41, {Located_In, 0.5895902908800758; Has_Job, 0.16210283293779865; Part_of_Org, 0.15818198928963584; _NR, 0.09012488689248967}
    EntityMention [type=O, objectId=EntityMention-41, hstart=40, hend=41, estart=40, eend=41, headPosition=40, value=".", corefID=-1]
    EntityMention [type=LOCATION, objectId=EntityMention-37, hstart=23, hend=24, estart=23, eend=24, headPosition=23, value="Krasnohorivka", corefID=-1]
]
"""
mock_response_short_text_str = """
Extracted the following MachineReading entity mentions:

Extracted the following MachineReading relation mentions:

"""
mock_response_no_text_str = ""
