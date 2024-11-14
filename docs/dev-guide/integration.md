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
    1. Make sure to create an Originator, Provider, and Source so that you can copy a valid source ID for the NLP API call
    2. If the CoreNLP container quits unexpectedly with no error message upon API call, allocate more resources to docker and try again
    3. Check out the Objects, Relationships, and Attributes!
