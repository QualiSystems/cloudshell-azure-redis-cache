from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadCommandContext, \
    AutoLoadAttribute, AutoLoadResource, AutoLoadDetails
from azure.mgmt.redis import RedisManagementClient
from azure.mgmt.redis.models import Sku, RedisCreateOrUpdateParameters
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials


class CloudshellAzureRedisCacheDriver(ResourceDriverInterface):
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
        self._deploy_redis_cache_internal(context)

    def _deploy_redis_cache_internal(self, resource_context):
        rc = RedisContext(resource_context, self._get_azure_attributes(resource_context))
        rmc = self._get_redis_management_client(rc.subscription_id, rc.client_id, rc.secret, rc.tenant_id)
        redis_cache = rmc.redis.create_or_update(rc.resource_group, rc.cache_name,
                                                 RedisCreateOrUpdateParameters(
                                                     sku=Sku(name='Basic', family='C', capacity=1),
                                                     location=rc.region))

    def _get_redis_management_client(self, subscription_id, client_id, secret, tenant):
        credentials = ServicePrincipalCredentials(client_id=client_id, secret=secret, tenant=tenant)
        ResourceManagementClient(credentials, subscription_id).providers.register('Microsoft.Cache')
        return RedisManagementClient(credentials, subscription_id)

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


class RedisContext:
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
        self._cache_name = context.resource.attributes['Cache Name']
        self._resource_group = context.reservation.reservation_id

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
    def cache_name(self):
        return self._cache_name
