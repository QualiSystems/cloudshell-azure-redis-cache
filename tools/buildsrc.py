import zipfile
import os

our_path = os.path.dirname(os.path.realpath(__file__))
deployment_path = os.path.join(our_path, '..', 'deployment')
cloudshell_package_resource_driver_path = os.path.join(our_path, '..', 'cloudshell_package', 'Resource Drivers - Python')
cloudshell_package_topology_driver_path = os.path.join(our_path, '..', 'cloudshell_package', 'Topology Scripts')

if not os.path.exists(deployment_path):
    os.makedirs(deployment_path)

cdn_path = os.path.join(our_path, '..', 'src', 'cdn_deployer')
redis_path = os.path.join(our_path, '..', 'src', 'redis_deployer')
sandbox_setup_path = os.path.join(our_path, '..', 'src', 'DefaultSandboxSetupForAzureServices')
media_services_path = os.path.join(our_path, '..', 'src', 'media_services')
cloudshell_package_path = os.path.join(our_path, '..', 'cloudshell_package')


def get_files(path):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            relDir = os.path.relpath(dirpath, path)
            relFile = os.path.join(relDir, filename)
            files.append(relFile)
    return files

cdn_deployer_files = get_files(cdn_path)
redis_deployer_files = get_files(redis_path)
media_services_files = get_files(media_services_path)
sandbox_setup_files = get_files(sandbox_setup_path)
cloudshell_package_files = get_files(cloudshell_package_path)


def zippit(source_path, zip_name, files, destination_path):
    with zipfile.ZipFile(os.path.join(destination_path, zip_name), mode='w') as zf:
        for file in files:
            zf.write(os.path.join(source_path, file), arcname=file)


zippit(cdn_path, 'cdn_deployment.zip', cdn_deployer_files, deployment_path)
zippit(redis_path, 'redis_deployer.zip', redis_deployer_files, deployment_path)
zippit(media_services_path, 'media_services_deployer.zip', media_services_files, deployment_path)
zippit(sandbox_setup_path, 'sandbox_setup.zip', sandbox_setup_files, deployment_path)

zippit(cdn_path, 'CDN Endpoint Deployer.zip', cdn_deployer_files, cloudshell_package_resource_driver_path)
zippit(redis_path, 'Redis Deployer.zip', redis_deployer_files, cloudshell_package_resource_driver_path)
zippit(media_services_path, 'Media Service Deployer.zip', media_services_files, cloudshell_package_resource_driver_path)
zippit(sandbox_setup_path, 'Default Sandbox Setup.zip', sandbox_setup_files, cloudshell_package_topology_driver_path)

zippit(cloudshell_package_path, 'cloudshell_package.zip', cloudshell_package_files, deployment_path)


