#!/usr/bin/python

import os
import time
import xmlrpclib
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from urllib2 import HTTPError

import poaupdater.uLogging
from poaupdater import openapi
from poaupdater import apsapi
from poaupdater.openapi import OpenAPIError
from poaupdater.uConfig import Config


class OaError(Exception):
    def __init__(self, msg=None, innerexc=None):
        Exception.__init__(self, msg)
        self.innerexc = innerexc


class OaLicense:
    def __init__(self, license_file):
        if not os.path.exists(license_file):
            raise OaError("License file %s not found" % license_file)
        if not os.access(license_file, os.R_OK):
            raise OaError("License file %s not readable" % license_file)
        self.content = open(license_file, "r").read()
        try:
            self._xml = ET.parse(license_file)
            self.key_number = self._xml.find('{http://parallels.com/schemas/keys/core/3}key-number').text
        except ParseError as e:
            raise OaError("Failed to parse XML in %s" % license_file, e)
        except AttributeError as e:
            raise OaError("Failed to read key number from %s" % license_file, e)


class OaApi:
    
    class _method:
        def __init__(self, api, name):
            self.name = name
            self.api = api
        def __repr__(self):
            return '<OA OpenAPI method: %s>' % name
        def __getattr__(self, name):
            if self.name == '':
                return self.__class__(self.api, name)
            else:
                return self.__class__(self.api, '%s.%s' % (self.name, name))
    class _sync_method(_method):
        def __call__(self, **kwargs):
            return self.api.sync_call(self.name, **kwargs)
    class _async_method(_method):
        def __call__(self, **kwargs):
            return self.api.async_call(self.name, **kwargs)
    class _asyncw_method(_method):
        def __call__(self, **kwargs):
            return self.api.async_call_wait(self.name, **kwargs)

    class _aps_method:
        def __init__(self, api, verb, path='/aps/2/'):
            self.api = api
            self.verb = verb
            self.path = path
        def __repr__(self):
            return "<OA APS REST API %s %s%s>" % (self.verb, self.api._apsc_uri, self.path)
        def __getattr__(self, path):
            return self.__class__(self.api, self.verb, self.path + path + '/')
        def __getitem__(self, index):
            return self.__class__(self.api, self.verb, self.path + str(index) + '/')
        def __call__(self, **kwargs):
            return self.api.aps_call(self.verb, self.path, **kwargs)
    
    async_timeout = 120
    
    def __init__(self, logfile=None):
        self.init_logging(filename=logfile)
        openapi.initFromEnv(Config())
        self._api = openapi.OpenAPI()
        self.sync = OaApi._sync_method(self, '')
        self.async = OaApi._async_method(self, '')
        self.asyncw = OaApi._asyncw_method(self, '')
        self.get_aps_token()
        self._apsapi = apsapi.API(self._apsc_uri)
        self.GET = OaApi._aps_method(self, 'GET')
        self.PUT = OaApi._aps_method(self, 'PUT')
        self.POST = OaApi._aps_method(self, 'POST')
        self.DELETE = OaApi._aps_method(self, 'DELETE')
    
    def init_logging(self, filename=None):
        poaupdater.uLogging.log_to_console = False
        # optionally, save to a file
        poaupdater.uLogging.logfile = open(filename or 'api.log', 'w')
    
    def sync_call(self, methodname, **kwargs):
        """Run sync api call
        
        :returns: response from api call
        """
        #TODO lock api until commit
        method = getattr(self._api, methodname)
        try:
            result = method(**kwargs)
        except OpenAPIError as e:
            raise OaError("OpenAPI error: %s" % e.error_message, e)
        return result
    
    def get_aps_token(self):
        res = self.sync.pem.APS.getAccountToken(account_id=1, subscription_id=0)
        self._aps_token = res['aps_token']
        self._apsc_uri = res['controller_uri']
    
    def aps_call(self, verb, path, rql=None, headers=None, data=None):
        headers = headers or {}
        headers['APS-Token'] = self._aps_token
        p = path + rql if rql else path
        try:
            res = self._apsapi.call(verb, p, headers, data)
        except HTTPError as e:
            if e.code == 403 and hasattr(e, 'aps') and e.aps.message == 'Token expired':
                self.get_aps_token()
                headers['APS-Token'] = self._aps_token
                res = self._apsapi.call(verb, p, headers, data)
            else:
                raise e
        return res

    def async_call(self, methodname, **kwargs):
        """Run async api call
        
        :returns: (request_id, response)
        """
        #TODO lock api until commit
        method = getattr(self._api, methodname)
        try:
            request_id = self._api.beginRequest()
            result = method(**kwargs)
            self._api.commit()
        except OpenAPIError as e:
            raise OaError("OpenAPI error: %s" % e.error_message, e)
        return request_id, result
    
    def get_request_status(self, request_id):
        return self._api.pem.getRequestStatus(request_id=request_id)

    def is_running_request(self, request_id):
        st = self.get_request_status(request_id)
        return st['request_status'] == 1

    def is_failed_request(self, request_id):
        st = self.get_request_status(request_id)
        return st['request_status'] == 2

    def async_call_wait(self, methodname, timeout=None, **kwargs):
        """Run async api call and wait till execution
        
        :returns: response from api call
        :raises OaError: in case of timeout or API call failure
        """
        timeout = timeout or self.async_timeout
        start_time = time.time()
        request_id, result = self.async_call(methodname, **kwargs)
        while True:
            status = self.get_request_status(request_id)
            if status['request_status'] == 0:
                return result
            elif status['request_status'] == 2:
                raise OaError("Failure while executing {0} with args {1}, status: {2}"
                    .format(methodname, kwargs, status))
            if time.time() - start_time > timeout:
                raise OaError("Timeout ({2}) while executing {0} with args {1}"
                    .format(methodname, kwargs, timeout))
            time.sleep(timeout/20.0)
    
    def list_methods(self):
        return getattr(self._api.server, 'system.listMethods')({})
    
    def get_method_signature(self, method_name):
        return self.sync.pem.getMethodSignature(method_name=method_name)

    def has_active_license(self):
        try:
            self.sync.pem.checkLicenseIsActive()
        except OaError as e:
            ie = e.innerexc
            if ie and isinstance(ie, OpenAPIError) and ie.module_id == 'Licensing' and ie.extype_id == 1:
                return False
            else:
                raise e
        return True

    def upload_license(self, license):
        self.sync.pem.uploadLicense(license=xmlrpclib.Binary(license.content))

    def remove_license(self, key_number):
        self.sync.pem.removeLicense(key_id=key_number)

    def get_license_number(self):
        if self.has_active_license():
            rql='?implementing(http://parallels.com/aps/types/pa/productLicense/1.1)'
            return self.GET.resources(rql=rql)[0].keyNumber
        else:
            return None

    def get_aps_type_schema(self, typeid):
        res = self.GET.types(rql='?id='+typeid)
        if not res:
            return None
        res = res[0]
        if '#' in typeid:
            structure_name = typeid.split('#')[1]
            res = res.structures[structure_name]
            res['name'] = structure_name
            res['id'] = typeid
        return res

    def get_installed_modules(self):
        return self.sync.pem.packaging.listInstalledModules()

    def install_module(self, module_name):
        """ List of available modules:
        [root@oss ~]# grep 'MODULE id=' oa-7.1-3256/*/*/*.mdl | grep -v hide_everywhere | grep -v essentials | awk -F'"' '{print "\"" $2 "\": " $6 }'
        "PBA": Billing
        "LegacyMigration": Legacy Migration Manager
        "Migration": Migration Manager
        "saml2-idp": SAML2 Identity Provider
        "Linux Mail": Linux Mail Hosting
        "Messaging and Collaboration": Messaging and Collaboration
        "PACI": Cloud Infrastructure
        "Platform": Platform
        "Linux Shared": Linux Shared Hosting
        "Windows Shared": Windows Shared Hosting
        "SHM": WebHosting Plesk
        "Parallels Panel": Plesk
        "Virtualization": Virtualization (Virtuozzo containers)
        """
        self.asyncw.pem.packaging.installModule(short_name=module_name)
        self.asyncw.pem.packaging.toggleModuleUIConfigurationOnHosts(short_name=module_name, enable=True)

    def is_node_registered(self, backnet):
        rql = '?implementing(http://www.parallels.com/pa/pa-core-services/host-management/Host)'
        hosts = self.GET.resources(rql=rql)
        return backnet in [h['backnetIp'] for h in hosts]

    def register_shared_node(self, backnet, login, password, frontnet=None,
            new_hostname=None, role=None, role_params=None):
        shared_ip = frontnet or backnet
        net_conf = {'communication_ip': backnet, 'shared_ip': shared_ip}
        if role_params:
            _role_params = [ {'name': n, 'value': v} for n, v in role_params.items() ]
        else:
            _role_params = None
        res = self.asyncw.pem.registerSharedNode(host=backnet, login=login, password=password,
                network_config=net_conf, new_hostname=new_hostname,
                role=role, role_params=_role_params)
        return res.get('host_id')

    def register_dns(self, backnet, login, password, frontnet, new_hostname=None):
        return self.register_shared_node(backnet, login, password, frontnet, new_hostname, role='DNS_BIND')
