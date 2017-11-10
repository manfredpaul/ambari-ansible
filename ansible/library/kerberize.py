#!/usr/bin/python
import urllib
import urllib2,base64,json
import os.path

# Set headers, including authentication headers
def get_headers(username,password):
	base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
	headers = { 'X-Requested-By': 'ambari', 'Authorization': 'Basic '+base64string }
	return headers

# Get security tyoe
def get_security_type(ambari_address, ambari_port, username, password, clustername):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return results['Clusters']['security_type']

def get_request_status(url, username, password):
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return (results['Requests']['request_status'],results['Requests']['progress_percent'])

def wait_for_request(url, username, password, timeout):
	start = time.time()
	while True:
		status,percentage = get_request_status(url, username, password)
		if status.lower() == 'completed':
			return True
		elif status.lower() == 'failed':
			module.fail_json(msg='Request has failed after: '+str(time.time() - start)+'s'+
			' with status: '+ status + ' and percent complete: '+str(percentage))
		elif timeout != 0 and (time.time() - start) > timeout:
			module.fail_json(msg='Request has timed out after: '+str(time.time() - start)+'s'+
			' with status: '+ status + ' and percent complete: '+str(percentage))

def enable_kerberos(ambari_address, ambari_port, username, password, clustername, kdcprincipal, kdcpassword, wait_for_build, build_timeout):
	security_type = get_security_type(ambari_address, ambari_port, username, password, clustername)
	if security_type == 'KERBEROS':
		return False
	elif security_type != 'NONE':
		module.fail_json(msg='Unknown security type: '+security_type)
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername
	payload = '{"session_attributes" : {"kerberos_admin" : {"principal" : "'+kdcprincipal+'","password" : "'+kdcpassword+'"}}, "Clusters": {"security_type" : "KERBEROS"}}'
	req = urllib2.Request(url, data=payload, headers=get_headers(username,password))
	req.get_method = lambda: 'PUT'
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to post config: '+str(error.read()))
	results = json.loads(response.read())
	request_url = results['href']
	if wait_for_build:
		wait_for_request(request_url,username, password,build_timeout)
	return True

# Return list of service names
def get_cluster_services(ambari_address, ambari_port, username, password, clustername):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	service_names = list()
	for c_entry in results['items']:
		service_names.append(c_entry['ServiceInfo']['service_name'])
	return service_names

# Return list of service component names
def get_service_components(ambari_address, ambari_port, username, password, clustername, service):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services/'+service+'/components'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	comp_names = list()
	for c_entry in results['items']:
		comp_names.append(c_entry['ServiceComponentInfo']['component_name'])
	return comp_names

# Return status of service
def get_service_status(ambari_address, ambari_port, username, password, clustername, service):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services/'+service
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return results['ServiceInfo']['state']

# Post kerberos service
def post_kerberos_service(ambari_address, ambari_port, username, password, clustername):
	if 'KERBEROS' in get_cluster_services(ambari_address, ambari_port, username, password, clustername):
		return False
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services/KERBEROS'
	req = urllib2.Request(url, headers=get_headers(username,password))
	req.get_method = lambda: 'POST'
	response = urllib2.urlopen(req)
	return True

def put_service_in_state(ambari_address, ambari_port, username, password, clustername, service, state):
	if service == 'ALL':
		url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services'
	else:
		url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services/'+service
	req = urllib2.Request(url, data='{"ServiceInfo": {"state" : "'+state+'"}}', headers=get_headers(username,password))
	req.get_method = lambda: 'PUT'
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	request_url = results['href']
	return request_url

# Install kerberos service
def install_kerberos_service(ambari_address, ambari_port, username, password, clustername, wait, timeout):
	if 'KERBEROS' in get_cluster_services(ambari_address, ambari_port, username, password, clustername):
		if get_service_status(ambari_address, ambari_port, username, password, clustername, 'KERBEROS') != 'INIT':
			return False
	request_url = put_service_in_state(ambari_address, ambari_port, username, password, clustername,'KERBEROS','INSTALLED')
	if wait:
		wait_for_request(request_url,username, password, timeout)
	return True

def change_all_service_state(ambari_address, ambari_port, username, password, clustername, wait, timeout, state):
	service_changed = False
	for service in get_cluster_services(ambari_address, ambari_port, username, password, clustername):
		service_state = get_service_status(ambari_address, ambari_port, username, password, clustername, service)
		if service_state != 'STARTED' and service_state != 'INSTALLED':
			module.fail_json(msg='Cannot put service: '+service+' into state: '+state+' as it has unhandleable state: '+service_state)
		if state != service_state:
			service_changed = True
	if not service_changed:
		return False
	request_url = put_service_in_state(ambari_address, ambari_port, username, password, clustername, 'ALL', state)
	if wait:
		wait_for_request(request_url,username, password, timeout)
	return True

# Post kerberos service
def post_kerberos_client_component(ambari_address, ambari_port, username, password, clustername):
	if 'KERBEROS_CLIENT' in get_service_components(ambari_address, ambari_port, username, password, clustername, 'KERBEROS'):
		return False
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/services/KERBEROS/components/KERBEROS_CLIENT'
	req = urllib2.Request(url, headers=get_headers(username,password))
	req.get_method = lambda: 'POST'
	response = urllib2.urlopen(req)
	return True

# Return list of service component names
def get_desired_config_names(ambari_address, ambari_port, username, password, clustername):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	conf_names = results['Clusters']['desired_configs'].keys()
	return conf_names

def post_service_config(ambari_address, ambari_port, username, password, clustername, config_path):
	existing_configs = get_desired_config_names(ambari_address, ambari_port, username, password, clustername)
	if 'krb5-conf' in existing_configs and 'kerberos-env' in existing_configs:
		return False
	if not os.path.isfile(config_path):
		module.fail_json(msg='Cannot find config file: '+config_path)
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername
	config_file = open(config_path,'r')
	config = config_file.read()
	req = urllib2.Request(url, data=config, headers=get_headers(username,password))
	req.get_method = lambda: 'PUT'
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to post config: '+str(error.read()))
	return True

def get_host_components(ambari_address, ambari_port, username, password, clustername, host):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/hosts/'+host+'/host_components'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	comp_names = list()
	for c_entry in results['items']:
		comp_names.append(c_entry['HostRoles']['component_name'])
	return comp_names


def post_host_component(ambari_address, ambari_port, username, password, clustername, host):
	if 'KERBEROS_CLIENT' in get_host_components(ambari_address, ambari_port, username, password, clustername, host):
		return False
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+clustername+'/hosts?Hosts/host_name='+host
	req = urllib2.Request(url, data='{"host_components" : [{"HostRoles" : {"component_name":"KERBEROS_CLIENT"}}]}', headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	return True

def post_hosts_component(ambari_address, ambari_port, username, password, clustername, hosts):
	changed = False
	for host in hosts:
		host_changed = post_host_component(ambari_address, ambari_port, username, password, clustername, host)
		if host_changed:
			changed = True
	return changed

def main():
	# Use ansible module to parse arguments
	global module
	module = AnsibleModule(
		argument_spec = dict(
			action=dict(required=True, choices=['get_security_type','1_add_service','2_add_service_component','3_post_config','4_post_hosts_component',
			'5_install_kerberos_service','6_stop_all_services','7_enable_kerberos', '8_start_all_services']),
			cluster_name=dict(required=True, type='str'),
			config_path=dict(type='str'),
			hosts=dict(type='str'),
			kdc_admin_principal=dict(type='str'),
			kdc_admin_password=dict(type='str'),
			wait=dict(default=False, type='bool'),
			timeout=dict(default=300, type='int'),
			ambari_address=dict(default='localhost', type='str'),
			ambari_port=dict(default='8080', type='str'),
			username=dict(default='admin', type='str'),
			password=dict(default='admin', type='str')
		)
	)
	if module.params['action'] == 'get_security_type':
		security_type = get_security_type( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'])
		module.exit_json(changed=False, ansible_facts={'cluster_security': security_type }, comments='Cluster security type is: '+security_type)
	elif module.params['action'] == '1_add_service':
		changed = post_kerberos_service( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'])
		if changed:
			module.exit_json(changed=True, comments='Service added to cluster')
		else:
			module.exit_json(changed=False, comments='Service already in cluster')
	elif module.params['action'] == '2_add_service_component':
		changed = post_kerberos_client_component( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'])
		if changed:
			module.exit_json(changed=True, comments='Service component added to cluster')
		else:
			module.exit_json(changed=False, comments='Service component already in cluster')
	elif module.params['action'] == '3_post_config':
		if 'config_path' not in module.params.keys():
			module.fail_json(msg='You must specify a config file for this action')
		changed = post_service_config( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],module.params['config_path'])
		if changed:
			module.exit_json(changed=True, comments='Config added to cluster')
		else:
			module.exit_json(changed=False, comments='Config already in cluster')
	elif module.params['action'] == '4_post_hosts_component':
		if 'hosts' not in module.params.keys():
			module.fail_json(msg='You must specify hosts for this action')
		host_list =  module.params['hosts'].split(',')
		changed = post_hosts_component( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],host_list)
		if changed:
			module.exit_json(changed=True, comments='Component added to hosts')
		else:
			module.exit_json(changed=False, comments='Components already on hosts')
	elif module.params['action'] == '5_install_kerberos_service':
		changed = install_kerberos_service( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],module.params['wait'],module.params['timeout'])
		if changed:
			module.exit_json(changed=True, comments='Service installed to cluster')
		else:
			module.exit_json(changed=False, comments='Service already install into cluster')
	elif module.params['action'] == '6_stop_all_services':
		changed = change_all_service_state( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],module.params['wait'],module.params['timeout'],'INSTALLED')
		if changed:
			module.exit_json(changed=True, comments='Services stopped on cluster')
		else:
			module.exit_json(changed=False, comments='Service already stopped on cluster')
	elif module.params['action'] == '7_enable_kerberos':
		if 'kdc_admin_principal' not in module.params.keys() or 'kdc_admin_password' not in module.params.keys():
			module.fail_json(msg='You must specify a kdc_admin_principal and kdc_admin_password for this action')
		changed = enable_kerberos( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],module.params['kdc_admin_principal'],module.params['kdc_admin_password'],
			module.params['wait'],module.params['timeout'])
		if changed:
			module.exit_json(changed=True, comments='Kerberos enabled in cluster')
		else:
			module.exit_json(changed=False, comments='Kerberos already enabled in cluster')
	elif module.params['action'] == '8_start_all_services':
		changed = change_all_service_state( module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['cluster_name'],module.params['wait'],module.params['timeout'],'STARTED')
		if changed:
			module.exit_json(changed=True, comments='Services started on cluster')
		else:
			module.exit_json(changed=False, comments='Service already started on cluster')

# import module snippets
from ansible.module_utils.basic import *
main()