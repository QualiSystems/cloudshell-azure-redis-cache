#!/usr/bin/env python
# -*- coding: utf-8 -*-
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
import cloudshell.api.cloudshell_api as csapi
import test_constants as c
from uuid import uuid4
import time

"""
Tests for `CloudshellAzureMediaServicesDriver`
"""

import unittest
from driver import CloudshellAzureRedisCacheDriver


def mock_get_azure_attributes(context, *args):
    azure_attributes = dict()
    azure_attributes['Azure Subscription ID'] = c.SUBSCRIPTION_ID
    azure_attributes['Azure Client ID'] = c.CLIENT_ID
    azure_attributes['Azure Secret'] = c.SECRET
    azure_attributes['Azure Tenant'] = c.TENANT
    azure_attributes['Region'] = c.REGION
    return azure_attributes


def resource_management_client(azure_attributes):
    credentials = ServicePrincipalCredentials(client_id=azure_attributes['Azure Client ID'],
                                              secret=azure_attributes['Azure Secret'],
                                              tenant=azure_attributes['Azure Tenant'])
    rmc = ResourceManagementClient(credentials, azure_attributes['Azure Subscription ID'])
    return rmc


def create_resource_group(context):
    azure_attributes = mock_get_azure_attributes(context)
    rmc = resource_management_client(azure_attributes)
    resource_group_params = {'location': azure_attributes['Region']}
    rmc.resource_groups.create_or_update(context.reservation.reservation_id, resource_group_params)


def delete_resource_group(context):
    azure_attributes = mock_get_azure_attributes(context)
    rmc = resource_management_client(azure_attributes)
    delete_op = rmc.resource_groups.delete(context.reservation.reservation_id)
    delete_op.wait()


def mock_context():
    global context

    class Object(object):
        pass

    context = Object()
    context.resource = Object()
    context.resource.attributes = dict()
    context.resource.attributes['Tier'] = 'Basic'
    context.resource.attributes['Cache Capacity'] = '2'
    context.resource.name = 'lolwut'
    context.reservation = Object()
    context.reservation.reservation_id = str(uuid4())
    context.reservation.domain = 'Global'
    context.connectivity = Object()
    context.connectivity.server_address = 'localhost'
    context.connectivity.admin_auth_token = csapi.CloudShellAPISession(host=context.connectivity.server_address,
                                                                       domain=context.reservation.domain,
                                                                       username='admin',
                                                                       password='admin').token_id
    return context


api_session = csapi.CloudShellAPISession
api_session.SetServiceAttributesValues = lambda *args, **kwargs: None


class TestCloudshellAzureRedisCacheDriver(unittest.TestCase):
    def setUp(self):
        self.context = mock_context()
        create_resource_group(context)

    def tearDown(self):
        # can only delete once the redis cache has reached a certain stage
        # todo detect that redis cache is deleteable
        for i in range(10):
            try:
                delete_resource_group(context)
                break
            except Exception as e:
                if i == 9:
                    raise e
                else:
                    time.sleep(120)
                    continue

    def test_deploy_redis_cache(self):
        driver = CloudshellAzureRedisCacheDriver(get_azure_attributes_service=mock_get_azure_attributes,
                                                 api_session=api_session)
        driver.deploy(context, 'mocked cloud provider')


if __name__ == '__main__':
    import sys

    sys.exit(unittest.main())
