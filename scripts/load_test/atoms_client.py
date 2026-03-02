from oms_sdk import get_generated_graphql_client

from oms_sensemaking.config import SETTINGS

omsb_url = "http://localhost:8010/graphql"


class AtomsClient:
    def __init__(self, user_dn=""):
        self.client = get_generated_graphql_client(
            url=omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
            ssl_cert_file_path=SETTINGS.atoms_cacert_path,
        )


atoms_client = AtomsClient()
