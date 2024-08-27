from stanza.server import CoreNLPClient

CUSTOM_PROPS = {
    "annotators": "tokenize, pos, lemma, ner, depparse, relation",
    "ner.model": "src/oms_sensemaking/nlp/training/ner-model.ser",
}

PROPS = {"annotators": "tokenize, pos, lemma, ner, depparse, relation"}

text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."
russia_ukraine_text = (
    "The Pokrovsk area remains in Ukrainian hands, but Russian forces are pushing closer.\n\nFlags, "
    "beads and handwritten messages adorn a monument near Pokrovsk that marks a gateway to "
    "Ukraine’s Donetsk region.\nExhausted soldiers are spending longer in the trenches, "
    "Kucher said, because there are no fresh troops to replace them.\n\nSeveral months ago, "
    "he sent one of his platoon commanders, who goes by Zhak, to replace an exhausted soldier in a "
    "trench for a week.\n\nZhak returned in late July, after spending 50 days there. Three "
    "attempts at troop rotations had to be abandoned when Russian attacks began. Another soldier "
    "spent 105 days in the same trench and now is in the hospital recovering.\n\nZhak, "
    "who is 46 years old, got straight back to work.\n\n\n\nA mortar-battery commander with the "
    "call sign Fantom recounts efforts to spot and kill Russian scouts before they could give away "
    "Ukrainian positions.\n“The situation doesn’t allow me to even ask for days off—I’d feel bad "
    "leaving,” he said. “Once it stabilizes, I’ll ask for a break.”\n\nThe Russian assaults on "
    "motorbikes—which have become common up and down the eastern front this summer—make use of "
    "Moscow’s numerical advantage. The salvos are costly—most, or all, of the bikers are usually "
    "killed—but they help Russian forces locate Ukraine’s positions and secure a toehold that can "
    "be gradually reinforced.\n\nSitting in a 21st Battalion command bunker outside Krasnohorivka "
    "last week, a Wall Street Journal reporter watched a live drone feed as the five-bike assault "
    "unfolded. Drone teams began searching for the two who escaped. They quickly spotted one "
    "sheltering in the ruins of a house, then killed him with an explosive drone.\n\n\n\nAt a 21st "
    "Battalion command post, a live feed shows Russian troops charging toward Ukrainian positions "
    "on motorbikes.\n\nMembers of the 21st Battalion have been feeling the strain of a manpower "
    "shortage.\nBut they couldn’t find the last Russian, which posed a problem. If even one "
    "Russian survived, he could tell his colleagues exactly where the Ukrainians were located, "
    "then the Russians would shell those positions.\n\n“We’ve heard them on the radio saying, "
    "‘The enemy is firing from there, there, there,’ ” Fantom, the 28-year-old commander of the "
    "21st Battalion’s mortar battery, said from the command post. “The goal is to see where our "
    "troops are, then hit us with artillery or mortars or drones…That’s why it’s always better to "
    "kill all the witnesses.”\n\nEventually, a drone pilot said he had spotted the last Russian "
    "biker hiding under a burned-out car. Still, no one fired a mortar at him.\n\n\n\n\nUkrainian "
    "mortar teams in the area have to contend with long, risky stints on duty and limited "
    "ammunition.\n“If we had unlimited numbers, we’d try to hit the car,” said one soldier "
    "watching the live feed at the command post. “But we don’t have as much ammunition as we’d "
    "like. We can’t use a mortar to kill only one person.”\n\nOther brigades in the east "
    "complained of similar ammunition shortages.\n\n“We have orders only to shoot at stationary "
    "targets,” said Sifonesco, the 46-year-old commander of an artillery-reconnaissance unit "
    "working near Pokrovsk. “We have to wait for a tank to come to a stop before we can try to hit "
    "it."
)
with CoreNLPClient(properties=CUSTOM_PROPS, timeout=60000, memory="16G") as client:
    # submit the request to the server
    ann = client.annotate(russia_ukraine_text)  # Returns document type
    sentence = ann.sentence[0]
    # print(type(sentence.relation[0]))
    # print(type(sentence.mentions[0]))

    for sentence in ann.sentence:
        for mention in sentence.mentions:
            print(mention)
        for relation in sentence.relation:
            print(relation.type)
            if relation.type != "_NR":
                print(sentence.relation)

    # get the first sentence
    # sentence = ann.sentence[0]
    # print("Relations:")
    # print(sentence.relation)  # This works
    # print("Mentions:")
    # print(sentence.mentions)

    # mentions = sentence.mentions

    # print(type(sentence))
    # print(type(mentions))
    # print(mentions)

    # get the dependency parse of the first sentence
    # print('---')
    # print('dependency parse of first sentence')
    # dependency_parse = sentence.basicDependencies
    # print(dependency_parse)

    # #get the tokens of the first sentence
    # #note that 1 token is 1 node in the parse tree, nodes start at 1
    # print('---')
    # print('Tokens of first sentence')
    # for token in sentence.token :
    #     print(token)
    # print(token.value, token.pos, token.ner)
