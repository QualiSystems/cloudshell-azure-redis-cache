from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadCommandContext, \
    AutoLoadAttribute, AutoLoadResource, AutoLoadDetails
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.cdn.models import ProfileCreateParameters, Sku, SkuName, EndpointCreateParameters, \
    QueryStringCachingBehavior, DeepCreatedOrigin
from uuid import uuid4


class CloudshellAzureCdnDeployerDriver(ResourceDriverInterface):
    def __init__(self, get_azure_attributes_service=None):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        if get_azure_attributes_service is None:
            self._get_azure_attributes = get_azure_attributes
        else:
            self._get_azure_attributes = get_azure_attributes_service

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def deploy(self, context):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """
        self._deploy_cdn_service(context)

    def _deploy_cdn_service(self, resource_context):
        rc = CdnContext(resource_context, self._get_azure_attributes(resource_context))
        cmc = self._get_cdn_management_client(rc.subscription_id, rc.client_id, rc.secret, rc.tenant_id)
        profile_properties = ProfileCreateParameters(location=rc.region,
                                                     sku=Sku(name=SkuName.standard_akamai),
                                                     tags=dict())
        result = cmc.profiles.create(rc.profile_name, profile_properties, rc.resource_group)
        result.wait()
        dco = DeepCreatedOrigin(host_name=rc._origin_hostname, http_port=80, https_port=443, name=uuid4())
        endpoint_properties = EndpointCreateParameters(location=rc.region,
                                                       tags=dict(),
                                                       origin_host_header=rc.origin_host_header,
                                                       origin_path=rc.origin_path,
                                                       is_http_allowed=True,
                                                       is_https_allowed=True,
                                                       is_compression_enabled=True,
                                                       query_string_caching_behavior=QueryStringCachingBehavior.ignore_query_string,
                                                       content_types_to_compress=['text/plain', 'text/html', 'text/css',
                                                                                  'text/javascript', 'application/x-javascript',
                                                                                  'application/javascript', 'application/json',
                                                                                  'application/xml'],
                                                       origins=[dco]

                                                       )
        result = cmc.endpoints.create(uuid4(), endpoint_properties, rc.profile_name, rc.resource_group)
        print result

    def _get_cdn_management_client(self, subscription_id, client_id, secret, tenant):
        credentials = ServicePrincipalCredentials(client_id=client_id, secret=secret, tenant=tenant)
        cmc = CdnManagementClient(credentials, subscription_id)
        return cmc

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass


def get_azure_attributes(context):
    """
    :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
    :rtype dict(str):
    """
    api = CloudShellAPISession(host=context.connectivity.server_address,
                             token_id=context.connectivity.admin_auth_token,
                             domain=context.reservation.domain)
    azure_resource_name = context.resource.attributes['Azure Resource']
    azure_resource = api.GetResourceDetails(azure_resource_name)
    azure_attributes = {resattr.Name: resattr.Value for resattr in azure_resource.ResourceAttributes}
    return azure_attributes


class CdnContext:
    def __init__(self, context, azure_attributes):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :return:
        """
        self._subscription_id = azure_attributes['Azure Subscription ID']
        self._client_id = azure_attributes['Azure Client ID']
        self._secret = azure_attributes['Azure Secret']
        self._tenant_id = azure_attributes['Azure Tenant']
        self._region = azure_attributes['Region']
        self._resource_group = context.reservation.reservation_id
        self._profile_name = context.resource.attributes['Profile Name']
        self._origin_hostname = context.resource.attributes['Endpoint Origin Host Name']
        self._origin_host_header = context.resource.attributes['Endpoint Origin Host Header']
        self._origin_path = context.resource.attributes['Endpoint Origin Path']

    @property
    def origin_hostname(self):
        return self._origin_hostname

    @property
    def origin_host_header(self):
        return self._origin_host_header

    @property
    def origin_path(self):
        return self._origin_path

    @property
    def subscription_id(self):
        return self._subscription_id

    @property
    def client_id(self):
        return self._client_id

    @property
    def secret(self):
        return self._secret

    @property
    def tenant_id(self):
        return self._tenant_id

    @property
    def region(self):
        return self._region

    @property
    def resource_group(self):
        return self._resource_group

    @property
    def profile_name(self):
        return self._profile_name
