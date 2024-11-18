# Integrating Sensemaking with other OMS services

### Steps to see NLP Sensemaker objects with Chronicle
This may have heavy overlap with the Geospatial Sensemaker.

1. Repos needed: `chronicle-ui`, `dime-local-dev-env`, `oms-sensemaking`
2. In `oms-sensemaking`
   1. Update the `.env` file to include the desired `OMSB_VERSION` (Grimlock-INC-7 or 8)
   2. Run `docker compose up`
   3. Navigate to the API at http://localhost:5001/docs#/ 
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
          1. Make sure to create an Originator, Provider, and Source in Chronicle so that you can copy a valid source ID for the NLP API call
          2. If the CoreNLP container quits unexpectedly with no error message upon API call, allocate more resources to docker and try again
          3. Check out the Objects, Relationships, and Attributes!
          4. Here is a sample request with the `source_id` and `text` fields filled out. You must change the `source_id` for it to work, but feel free to use this text sample. It is followed by what might appear in Chronicle: 
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

