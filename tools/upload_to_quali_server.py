from qpm.packaging.quali_api_client import QualiAPIClient
import os

our_path = os.path.dirname(os.path.realpath(__file__))

host = 'localhost'
port = '9000'
username = 'admin'
password = 'admin'
domain = 'Global'

package_full_path = deployment_path = os.path.join(our_path, '..', 'deployment', 'cloudshell_package.zip')

if os.path.isfile(package_full_path):
    server = QualiAPIClient(host, port, username, password, domain)
    server.upload_environment_zip_file(package_full_path)