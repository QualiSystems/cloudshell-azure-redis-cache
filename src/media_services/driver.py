from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext
from azure.mgmt.media import MediaServicesManagementClient
from azure.mgmt.media.models import MediaService
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.media.models import StorageAccount
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
import re
from uuid import uuid4


class CloudshellAzureMediaServicesDriver(ResourceDriverInterface):
    def __init__(self, get_azure_attributes_service=None, api_session=None):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        if get_azure_attributes_service is None:
            self._get_azure_attributes = get_azure_attributes
        else:
            self._get_azure_attributes = get_azure_attributes_service
        if api_session is None:
            self._api_session = CloudShellAPISession
        else:
            self._api_session = api_session

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
        return self._deploy_media_services(context, cloud_provider)

    def _get_storage_account_from_reservation(self, media_services_context):
        smc = self._get_storage_management_client(media_services_context.subscription_id,
                                                  media_services_context.client_id,
                                                  media_services_context.secret,
                                                  media_services_context.tenant_id)
        storage_accounts = smc.storage_accounts.list_by_resource_group(media_services_context.resource_group)
        for storage_account in storage_accounts:
            try:
                if storage_account.tags['ReservationId'] == media_services_context.resource_group:
                    return StorageAccount(id=storage_account.id, is_primary=True)
            except:
                continue
        raise Exception('Could not find storage account in resource group ' + str(media_services_context.resource_group))

    def _deploy_media_services(self, resource_context, cloud_provider):
        resid = resource_context.reservation.reservation_id
        api = _get_api(resource_context, self._api_session)
        resource_context.resource.attributes['Azure Resource'] = cloud_provider
        mc = MediaServicesContext(resource_context, self._get_azure_attributes(resource_context, api))
        msc = self._get_media_services_client(mc.subscription_id, mc.client_id, mc.secret, mc.tenant_id)
        storage_account = self._get_storage_account_from_reservation(mc)
        result = msc.media_service.create(mc.resource_group, mc.media_service_name,
                                          MediaService(location=mc.region, tags={'ReservationId': resid},
                                                       storage_accounts=[storage_account]))
        api.SetServiceAttributesValues(resid, resource_context.resource.name,
                                       [AttributeNameValue('Media Service Name', mc.media_service_name)])
        return 'Azure Service Deployed >> \'Media Service Name\': \'{0}\''.format(mc.media_service_name)

    def _get_media_services_client(self, subscription_id, client_id, secret, tenant):
        credentials = ServicePrincipalCredentials(client_id=client_id, secret=secret, tenant=tenant)
        ResourceManagementClient(credentials, subscription_id).providers.register('Microsoft.Media')
        return MediaServicesManagementClient(credentials, subscription_id)

    def _get_storage_management_client(self, subscription_id, client_id, secret, tenant):
        credentials = ServicePrincipalCredentials(client_id=client_id, secret=secret, tenant=tenant)
        return StorageManagementClient(credentials, subscription_id)

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass


def _get_api(resource_context, api_session):
    return api_session(host=resource_context.connectivity.server_address,
                                token_id=resource_context.connectivity.admin_auth_token,
                                domain=resource_context.reservation.domain)


def get_azure_attributes(context, api=None):
    """
    :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
    :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
    :rtype dict(str):
    """
    if api is not None:
        api = _get_api(context, CloudShellAPISession)
    azure_resource_name = context.resource.attributes['Azure Resource']
    azure_resource = api.GetResourceDetails(azure_resource_name)
    azure_attributes = {resattr.Name: resattr.Value for resattr in azure_resource.ResourceAttributes}
    return azure_attributes


class MediaServicesContext:
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
        self._media_service_name = str(uuid4()).replace('-', '')[:-8]

        self.validate()

    def validate(self):
        if re.match('^[\w-]+$', self.media_service_name) is None:
            raise Exception('The media service name can contain only lowercase letters and numbers.')
        if len(self._media_service_name) < 3 or len(self._media_service_name) > 24:
            raise Exception('The media service name should be between 3 and 24 characters length')

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
    def media_service_name(self):
        return self._media_service_name
