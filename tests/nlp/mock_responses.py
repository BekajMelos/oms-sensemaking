"""Mock responses for NLP testing using the MockCoreNlpClient"""

mock_response_long_text = [
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
mock_response_normal_text = [
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
mock_response_short_text = [
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
mock_response_bunched_text = [
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
mock_response_no_text = []
