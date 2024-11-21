# Integrating Sensemaking with other OMS services

### Steps to see NLP Sensemaker objects with Chronicle

This may have heavy overlap with the Geospatial Sensemaker.

1. Repos needed: `chronicle-ui`, `dime-local-dev-env`, `oms-sensemaking`
2. In `oms-sensemaking`
   1. Update the `.env` file to include the desired `OMSB_VERSION` (Grimlock-INC-7 or 8)
   2. Run `docker compose up`
   3. Navigate to the API at http://localhost:5001/docs
      1. If you are having issues getting this url to load, ensure the following block is in your `.env`:
      ```
      # TLS configuration
      UVICORN_SSL_KEYFILE=/opt/common/pki/server.private
      UVICORN_SSL_CERTFILE=/opt/common/pki/server.public
      UVICORN_SSL_CERT_REQS=0
      UVICORN_PORT=443
      ```
3. In `dime-local-dev-env`
   1. Follow `dime-local-dev-env` setup steps: https://tex.gerbil-cloud.ts.net:3000/DevOps/dime-local-dev-env#quick-start
   2. Run `git checkout omsb-grimlock`
   3. copy `.env.CHRONICLE` to `.env`
   4. In `.env` update `IMAGE_OMS_BRIDGE` to point to the same `OMSB_VERSION` as the `.env` in Sensemaking
   5. Run `make up`
4. In `chronicle-ui`
   1. Follow the chronicle setup steps in the readme: https://tex.gerbil-cloud.ts.net:3000/oms/chronicle-ui#setup
   2. Git checkout main
   3. Run `npm install` and `npm start`
   4. Navigate to the chronicle page at https://localhost/apps/chronicle
      1. If you have issues getting the page to load, ensure you have downloaded all certificates from `chronicle-ui/etc/test-certs` and marked them as 'trusted'. To do this:
         1. Open the 'Keychain Access' app on your Macbook (`CMD+Space --> 'Keychain Access'`)
         2. Click 'login' on the left sidebar
         3. The downloaded certificates from the Chronicle repo should be listed
         4. For each cert, double click the name, click the arrow next to 'Trust', and select 'Always Trust' from the first dropdown next to 'When using this certificate'
         5. If you are still having issues, try closing/reopening Chrome and/or restarting your Macbook
5. Connect `dime-local-dev-env` to the sensemaking container
   1. Run `docker network ls`
   2. Copy the NETWORK ID from the result of that command
      ```
           NETWORK ID     NAME                         DRIVER    SCOPE
           2defa7295a06   dime-local-dev-env_default   bridge    local
      ```
   3. Run `docker ps` to find the name of the Sensemaking container
      1. It should be `oms-sensemaking-oms_sensemaking-1` or something similar
   4. Run `docker network connect <dime-local-network-ID-here> <sensemaking-container-name-here>`
6. Now you should be able to run the Sensemaking API endpoints and view the results published to OMS in Chronicle
   1. Make sure to create an Originator, Provider, and Source in Chronicle so that you can copy a valid source ID for the NLP API call. To do this:
      1. Click the 'Data Types' icon in the left sidebar
      2. Select 'Sourcing'
      3. On the Sourcing page, ensure you are on the 'Sources' tab and click 'Actions' and 'Add Source'
      4. Work through the creation steps. In creating a Source, you will also be prompted to create a Provider and Originator.
   2. If the CoreNLP container quits unexpectedly with no error message upon API call, allocate more resources to docker and try again
   3. Check out the Objects, Relationships, and Attributes! The Nodes/Relationships you see in Chronicle should resemble those in the response of the FastAPI call. (See below example)

- Below is a sample request with the `source_id` and `text` fields filled out. You must change the `source_id` for it to work, but feel free to use this text sample, which is an excerpt from `etc/data/russia-ukraine.txt`:

```
{
  "source_id": "2d2a5a4d-b43d-4763-af9e-6369285985be",
  "acm": {
    "accms": [],
    "atom_energy": [],
    "banner": "UNCLASSIFIED",
    "classif": "U",
    "disp_only": "",
    "disponly_to": [
      ""
    ],
    "dissem_countries": [
      "USA"
    ],
    "dissem_ctrls": [],
    "f_accms": [],
    "f_atom_energy": [],
    "f_clearance": [
      "u"
    ],
    "f_macs": [],
    "f_missions": [],
    "f_oc_org": [],
    "f_regions": [],
    "f_sar_id": [],
    "f_sci_ctrls": [],
    "f_share": [],
    "fgi_open": [],
    "fgi_protect": [],
    "macs": [],
    "non_ic": [],
    "oc_attribs": [
      {
        "missions": [],
        "orgs": [],
        "regions": []
      }
    ],
    "owner_prod": [
      "USA"
    ],
    "portion": "U",
    "rel_to": [],
    "sar_id": [],
    "sci_ctrls": [],
    "version": "2.1.0"
  },
  "text": "As Ukraine Invades Russia, Kyiv's Troops Are in Trouble on the Eastern Front Ukrainian soldiers are overmatched in some areas and deployments in the trenches can stretch for months  NEAR KRASNOHORIVKA, Ukraine—As Ukrainian troops poured into Russia's Kursk region last week, five Russian assault troops on motorbikes were zipping toward Ukraine's front line hundreds of miles to the east.  Two of the bikers were gunned down. Another turned back and fled. But the last two escaped into the trees, looking for a place to hunker down and await reinforcements.  This is one of the tactics Russia is using to take advantage of its vastly larger number of troops in the Donetsk region of eastern Ukraine, Russia's primary target and the site of intensified assaults this week despite Ukraine's incursion into Russia. Ukraine's threadbare troops are struggling to hold them back.  The 21st Battalion of Ukraine's Separate Presidential Brigade is fighting to keep Russian forces at bay, including with mortar fire near the town of Krasnohorivka.  Ukraine's Kursk operation has embarrassed President Vladimir Putin and given Kyiv the tactical initiative in one area for the first time in nearly a year. But it transferred troops and weapons from its already-creaking front lines to pull it off, a gamble that risks making a bad situation worse.  'We don't have enough people to do our job properly,' said the commander of the 21st Battalion of the Separate Presidential Brigade, which faced the Russian assault last week at the edge of the contested town of Krasnohorivka.  Russian forces have gained territory at a faster rate this summer than at any point since the first weeks of the war and are now pushing toward the logistical hub of Pokrovsk."
}
```

- The following Entity in the API Response would show up in Chronicle with `Name: Ukraine`, and `Class: Geographical Location` or `Entity`

```
    {
        "type": "Location",
        "objectId": "EntityMention-71",
        "uuid": "77d3ee8e-f906-4572-8f80-958486dc92f7",
        "hstart": "1",
        "hend": "2",
        "estart": "1",
        "eend": "2",
        "headPosition": "1",
        "value": "Ukraine",
        "corefID": "-1"
    },
```

- The following Relationship in the API Response would show up in Chronicle with `Start Object: Kyiv`, `Relationship: located in at some time`, `End Object: Ukraine`

```
{
        "type": "Located_In",
        "objectId": "RelationMention-13",
        "uuid": "c8ce0562-43e9-4cfb-b8c9-e7eb6c2c61aa",
        "start": "1",
        "end": "6",
        "relations": [
          "Located_In, 0.4126628720267475",
          "Has_Job, 0.21216090765746073",
          "Part_of_Org, 0.1998946200003775",
          "_NR, 0.17528160031541418"
        ],
        "entities": [
          {
            "type": "Location",
            "objectId": "EntityMention-75",
            "uuid": "31760e4f-7bc4-473f-b2d8-76bfb8ae2c2f",
            "hstart": "5",
            "hend": "6",
            "estart": "5",
            "eend": "6",
            "headPosition": "5",
            "value": "Kyiv",
            "corefID": "-1"
          },
          {
            "type": "Location",
            "objectId": "EntityMention-71",
            "uuid": "77d3ee8e-f906-4572-8f80-958486dc92f7",
            "hstart": "1",
            "hend": "2",
            "estart": "1",
            "eend": "2",
            "headPosition": "1",
            "value": "Ukraine",
            "corefID": "-1"
          }
        ]
      },
```

- Additionally, a `Report` Object should exist and have a `Relationship: describes` to every single Entity that it produced.
