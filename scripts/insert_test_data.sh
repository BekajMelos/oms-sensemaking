#!/bin/bash

# Script to insert test data for pagination testing
# This script uses the working GraphQL format from Postman collections

echo "=== Inserting Test Data for Pagination Testing ==="

# Set common variables
GRAPHQL_URL="https://localhost:8020/graphql"
USER_DN="cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us"
TEST_PREFIX="PAGINATION_TEST"

# Function to create a test node using the working format from Postman
create_test_node() {
    local node_name=$1
    local class_iri=$2
    
    echo "Creating test node: $node_name"
    
    curl -k -s $GRAPHQL_URL \
        -H "Content-Type: application/json" \
        -H "user_dn: $USER_DN" \
        -d "{
            \"query\": \"mutation { createNode(input: { name: \\\"$node_name\\\", classIri: \\\"$class_iri\\\", tier: PRIMARY, isNso: false, allegiance: \\\"USA\\\", tags: [\\\"Pagination Testing\\\", \\\"Test Data\\\"], acm: {version:\\\"2.1.0\\\",classif:\\\"U\\\",owner_prod:[\\\"USA\\\"],atom_energy:[],sar_id:[],sci_ctrls:[],disponly_to:[\\\"\\\"],dissem_ctrls:[\\\"\\\"],non_ic:[],rel_to:[],fgi_open:[],fgi_protect:[],portion:\\\"U\\\",banner:\\\"UNCLASSIFIED\\\",dissem_countries:[\\\"USA\\\"],accms:[],macs:[],oc_attribs:[{orgs:[],missions:[],regions:[]}],f_clearance:[\\\"u\\\"],f_sci_ctrls:[],f_accms:[],f_oc_org:[],f_regions:[],f_missions:[],f_share:[],f_sar_id:[],f_atom_energy:[],f_macs:[],disp_only:\\\"\\\"} }) { id name guideId } }\"
        }"
    
    echo ""
}

# Create test nodes with different types
echo "Creating test nodes..."

# Create military organization nodes
create_test_node "$TEST_PREFIX Battalion Alpha" "https://foundry.ai.mil/ontology/4901-001/MilitaryOrganization"
create_test_node "$TEST_PREFIX Battalion Beta" "https://foundry.ai.mil/ontology/4901-001/MilitaryOrganization"
create_test_node "$TEST_PREFIX Battalion Gamma" "https://foundry.ai.mil/ontology/4901-001/MilitaryOrganization"

# Create equipment nodes
create_test_node "$TEST_PREFIX Tank Alpha" "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"
create_test_node "$TEST_PREFIX Aircraft Beta" "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"

# Create facility nodes
create_test_node "$TEST_PREFIX Facility Alpha" "https://foundry.ai.mil/ontology/4901-001/Facility"
create_test_node "$TEST_PREFIX Facility Beta" "https://foundry.ai.mil/ontology/4901-001/Facility"

echo "=== Checking if data was created ==="
curl -k -s $GRAPHQL_URL \
    -H "Content-Type: application/json" \
    -H "user_dn: $USER_DN" \
    -d '{"query": "query { nodes(query: { pageParams: { page: 1, pageSize: 10 } }) { data { id name guideId } } }"}'

echo ""
echo "=== Test data insertion complete ==="