from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext
from azure.mgmt.redis import RedisManagementClient
from azure.mgmt.redis.models import Sku, RedisCreateOrUpdateParameters, SkuName, SkuFamily
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

    def deploy(self, context, cloud_provider):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """
        self._deploy_redis_cache_internal(context, cloud_provider)

    def _deploy_redis_cache_internal(self, resource_context, cloud_provider):
        resource_context.resource.attributes['Azure Resource'] = cloud_provider
        rc = RedisContext(resource_context, self._get_azure_attributes(resource_context))
        rmc = self._get_redis_management_client(rc.subscription_id, rc.client_id, rc.secret, rc.tenant_id)
        redis_cache = rmc.redis.create_or_update(rc.resource_group, rc.cache_name,
                                                 RedisCreateOrUpdateParameters(
                                                     sku=Sku(name=rc.sku_name,
                                                             family=rc.sku_family,
                                                             capacity=rc.sku_capacity),
                                                     location=rc.region,
                                                    tags={'ReservationId': rc.resource_group}))

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
        self._sku_name = self._get_sku_name(context.resource.attributes['Tier'])
        # Sku family is C for basic or standard, P for premium. https://docs.microsoft.com/en-us/rest/api/redis/redis
        self._sku_family = SkuFamily.c if self._sku_name in [SkuName.basic, SkuName.standard] else SkuFamily.p
        self._sku_capacity = self._get_sku_capacity(context.resource.attributes['Cache Capacity'])

    def _get_sku_capacity(self, capacity_string):
        try:
            capacity = int(capacity_string)
            if capacity not in range(7) and self.sku_family == SkuFamily.c:
                raise ValueError('Unsupported capacity value')
            else:
                if capacity not in range(1, 5) and self.sku_family == SkuFamily.p:
                    raise ValueError('Unsupported capacity value')
        except ValueError:
            raise Exception('Valid capacity values: \n Valid values: for Basic/Standard tiers: 0, 1, 2, 3, 4, 5, 6\n for Premium tier: 1, 2, 3, 4. ')
        return capacity

    @staticmethod
    def _get_sku_name(sku_name):
        switcher = {
            'basic': SkuName.basic,
            'standard': SkuName.standard
        }
        try:
            sku_name = switcher[sku_name.lower()]
        except KeyError:
            raise Exception('Unsupported Pricing Tier; valid values are Basic, Standard')
        return sku_name

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

    @property
    def sku_name(self):
        return self._sku_name

    @property
    def sku_family(self):
        return self._sku_family

    @property
    def sku_capacity(self):
        return self._sku_capacity
