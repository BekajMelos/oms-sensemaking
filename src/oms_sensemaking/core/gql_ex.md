```
While the gql library in Python doesn't directly support two-way SSL for its GraphQL clients, you can achieve this using a combination of the requests library and its SSL capabilities. Here's a step-by-step guide:
Step 1: Install the necessary libraries
Code

pip install gql requests
Step 2: Prepare your client certificate and key
Ensure you have your client certificate and private key in PEM format.
Step 3: Create a custom transport
We'll create a custom transport to integrate the SSL configuration with the gql client.
Python

import ssl
import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTrans
class SSLRequestsHTTPTransport(RequestsHTTPTransport):
    def __init__(self, *args, **kwargs):
        self.cert = kwargs.pop('cert', None)
        self.key = kwargs.pop('key', None)
        super().__init__(*args, **kwargs)

    def connect(self):
        self.session = requests.Session()
        if self.cert and self.key:
            self.session.cert = (self.cert, self.key)
Step 4: Use the custom transport
Python

client = Client(
    transport=SSLRequestsHTTPTransport(
        url='https://your-graphql-endpoint',
        cert='client.crt',
        key='client.key'
    ),
    fetch_schema_from_transport=True
)

query = gql("""
    query {
        # Your GraphQL query
    }
""")

result = client.execute(query)
print(result)
Explanation
Custom Transport:
The SSLRequestsHTTPTransport class extends the default RequestsHTTPTransport to include the cert and key parameters for the client certificate and key.
requests.Session:
We use a requests.Session object to manage the SSL connection, including the client certificate and key.
Client Initialization:
When creating the gql client, we pass the custom transport with the necessary SSL parameters.
Important Considerations
Certificate Validation:
Ensure the server certificate is properly validated to prevent man-in-the-middle attacks.
Certificate Authority (CA):
If your server uses a custom CA, you might need to configure the verify parameter in the transport to point to the CA certificate.
Security:
Two-way SSL enhances security, but you should still consider other security measures such as proper authentication and authorization mechanisms.
```

# Node request body
```
            """
            query node($filter: AuditFilter, $filter1: HistoryFilter, $filter2: AttributeFilter, $filter3: NodeRelationshipFilter, $filter4: ObservationFilter, $filter5: ObjectCollectionFilter, $filter6: CommentFilter, $query: IdQuery!) {
              node(query: $query) {
                id
                version
                acm
                tags
                guideId
                name
                tier
                classIri
                className
                ifcCodes
                allegiance
                allegianceAor
                currentAor
                isNso
                audits(filter: $filter) {
                  totalSize
                  rollupAcm
                }
                history(filter: $filter1) {
                  totalSize
                  rollupAcm
                }
                attributes(filter: $filter2) {
                  totalSize
                  rollupAcm
                }
                relationships(filter: $filter3) {
                  totalSize
                  rollupAcm
                }
                observations(filter: $filter4) {
                  totalSize
                  rollupAcm
                }
                objectCollections(filter: $filter5) {
                  totalSize
                  rollupAcm
                }
                comments(filter: $filter6) {
                  totalSize
                  rollupAcm
                }
                ontologyClass {
                  iri
                  source
                  version
                  citation
                  classification
                  name
                  description
                  aliases
                  superclassIris
                  defaultIfc
                }
                permissions
                latestKnownLocation {
                  id
                  version
                  acm
                  tags
                  attributeIri
                  attributeName
                  attributeValue
                  attributeDisplayValue
                  attributeNormalizedValue
                  attributeType
                  confidence
                  sourceId
                  nodeId
                  authorityValue
                  authoritySetBy
                  authoritySetAtTime
                  valueStart
                  valueEnd
                  isMutable
                  isReviewed
                  reviewedBy
                  reviewedAt
                }
                lastVerified {
                  timestamp
                  userId
                }
              }
            }
            """
```

# create originator
```
"""
mutation createOriginator($filter: AuditFilter, $filter1: HistoryFilter, $filter2: ProviderFilter, $input: CreateOriginatorInput!) {
  createOriginator(input: $input) {
    id
    version
    acm
    tags
    name
    description
    audits(filter: $filter) {
      totalSize
      rollupAcm
    }
    history(filter: $filter1) {
      totalSize
      rollupAcm
    }
    providers(filter: $filter2) {
      totalSize
      rollupAcm
    }
  }
}
"""
```
