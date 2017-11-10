#!/usr/bin/python
import urllib
import urllib2,base64,json
import os.path
import time

# Function to order blueprints for comparison
def ordered(obj):
	if isinstance(obj, dict):
		return sorted((k, ordered(v)) for k, v in obj.items())
	if isinstance(obj, list):
		return sorted(ordered(x) for x in obj)
	else:
		return obj

# Set headers, including authentication headers
def get_headers(username,password):
	base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
	headers = { 'X-Requested-By': 'ambari', 'Authorization': 'Basic '+base64string }
	return headers

# Return list of cluster names
def get_cluster_names(ambari_address, ambari_port, username, password):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	cluster_names = list()
	for c_entry in results['items']:
		cluster_names.append(c_entry['Clusters']['cluster_name'])
	return cluster_names

# Return list of blueprint names
def get_blueprint_names(ambari_address, ambari_port, username, password):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/blueprints'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	blueprint_names = list()
	for bp_entry in results['items']:
		blueprint_names.append(bp_entry['Blueprints']['blueprint_name'])
	return blueprint_names

# Get a specific blueprint
def get_blueprint(blueprint_name, ambari_address, ambari_port, username, password):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/blueprints/'+blueprint_name
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return results

# Get list of services supported by the stack
def get_stack_services(ambari_address, ambari_port, username, password, stack):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/stacks/HDP/versions/'+str(stack)+'/services'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	services = list()
	for service in results['items']:
		services.append(service['StackServices']['service_name'])
	return services

# Get blueprint recommendation for this service list and stack version
def get_recommendation( ambari_address, ambari_port, username, password, stack, hosts, service_list):
	allowed_services = get_stack_services(ambari_address, ambari_port, username, password, stack)
	for service in service_list:
		if service not in allowed_services:
			module.fail_json(msg='Service not allowed with this stack version:' +str(service)
			+' allowed services are: '+str(allowed_services))
	payload = { 'recommend': 'configurations', 'hosts': hosts, 'services': service_list }
	payload_json = json.dumps(payload)
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/stacks/HDP/versions/'+str(stack)+'/recommendations'
	req = urllib2.Request(url, data=payload_json, headers=get_headers(username,password))
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to get recommendation: '+str(error.read())+' with config: '+payload_json)
	results = json.loads(response.read())
	return results

# Merge these recommendations with blueprint, our blueprint takes preference
def get_merged_recommendation(blueprint_s, ambari_address, ambari_port, username, password, stack, host_list, service_list):
	blueprint = json.loads(blueprint_s)
	recommended = get_recommendation(ambari_address, ambari_port, username, password, stack, host_list, service_list)
	for r_key, r_value in recommended['resources'][0]['recommendations']['blueprint']['configurations'].iteritems():
		conf_item = None
		for i in xrange(len(blueprint['configurations'])):
			if r_key in blueprint['configurations'][i].keys():
				conf_item = i
		if conf_item is None:
			blueprint['configurations'].append({ r_key: { 'properties': { } } })
			conf_item = len(blueprint['configurations'])-1
		for p_key, p_value in r_value['properties'].iteritems():
			if not p_key in blueprint['configurations'][conf_item][r_key]['properties'].keys():
				blueprint['configurations'][conf_item][r_key]['properties'][p_key] = p_value
	return json.dumps(blueprint)

def get_registered_hosts(ambari_address, ambari_port, username, password):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/hosts'
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	hosts = list()
	for host in results['items']:
		hosts.append(host['Hosts']['host_name'])
	return hosts

def get_not_registered_hosts(ambari_address, ambari_port, username, password, host_list):
	reg_hosts = get_registered_hosts(ambari_address, ambari_port, username, password)
	missing_hosts = [item for item in host_list if item not in reg_hosts]
	return missing_hosts

def wait_for_api(ambari_address, ambari_port, username, password,timeout):
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/hosts'
	req = urllib2.Request(url, headers=get_headers(username,password))
	start = time.time()
	while True:
		try:
			response = urllib2.urlopen(req)
		except:
			pass
		else:
			return
		if timeout != 0 and (time.time() - start) > timeout:
			module.fail_json(msg='Waiting for Ambari API to be ready has timed out after: '+str(time.time() - start)+'s')
		time.sleep(3)

def wait_for_registered_hosts(ambari_address, ambari_port, username, password, host_list, timeout):
	start = time.time()
	while True:
		missing_hosts = get_not_registered_hosts(ambari_address, ambari_port, username, password, host_list)
		if not missing_hosts:
			return True
		elif timeout != 0 and (time.time() - start) > timeout:
			module.fail_json(msg='Register has timed out after: '+str(time.time() - start)+'s'+
			' for hosts: '+','.join(missing_hosts))
		time.sleep(3)

# Get current baseurl for ambari stack
def get_base_url(ambari_address, ambari_port, username, password, url):
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return results['Repositories']['base_url']

# Post a new ambari stack url
def post_base_url(ambari_address, ambari_port, username, password,stack_version,repo_id,os_type,base_url):
	os_type = os_type.replace('centos','redhat')
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/stacks/HDP/versions/'+str(stack_version)+'/operating_systems/'+os_type+'/repositories/HDP-'+str(stack_version)
	current_base_url = get_base_url(ambari_address, ambari_port, username, password, url)
	if current_base_url == base_url:
		return False
	payload = { "Repositories": { "base_url": base_url, "verify_base_url": True } }
	payload_s = json.dumps(payload)
	req = urllib2.Request(url, data=payload_s, headers=get_headers(username,password))
	req.get_method = lambda: 'PUT'
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to post base url to '+url+' with payload:\n'+payload_s+'\n with error: '+str(error.read()))
	return True

# Post a blurprint, return boolean if changed or not
def post_blueprint(blueprint_name, blueprint_path, ambari_address, ambari_port, username, password, recommend, stack_ver=None, host_list=None, service_list=None):
	if not os.path.isfile(blueprint_path):
		module.fail_json(msg='Cannot find blueprint file: '+blueprint_path)
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/blueprints/'+blueprint_name
	# Check if blueprint already exists, and if so get a copy and delete
	blueprint_names = get_blueprint_names(ambari_address, ambari_port, username, password)
	old_blueprint = None
	if blueprint_name in blueprint_names:
		old_blueprint = get_blueprint(blueprint_name, ambari_address, ambari_port, username, password)
		req = urllib2.Request(url, headers=get_headers(username,password))
		req.get_method = lambda: 'DELETE'
		response = urllib2.urlopen(req)
	# Read and post new blueprint
	blueprint_file = open(blueprint_path,'r')
	blueprint = blueprint_file.read()
	if recommend:
		blueprint = get_merged_recommendation(blueprint, ambari_address, ambari_port, username, password, stack_ver, host_list, service_list)
	req = urllib2.Request(url, data=blueprint, headers=get_headers(username,password))
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to post blueprint: '+str(error.read()))
	# Get new blueprint and check if it has changed
	new_blueprint = get_blueprint(blueprint_name, ambari_address, ambari_port, username, password)
	if ordered(old_blueprint) != ordered(new_blueprint):
		return True
	else:
		return False

# Get status of the build
def get_build_status(url, username, password):
	req = urllib2.Request(url, headers=get_headers(username,password))
	response = urllib2.urlopen(req)
	results = json.loads(response.read())
	return (results['Requests']['request_status'],results['Requests']['progress_percent'])
	
# Post cluster to ambari
def post_cluster(cluster_name, cluster_path, ambari_address, ambari_port, username, password, wait_for_build, build_timeout):
	if not os.path.isfile(cluster_path):
		module.fail_json(msg='Cannot find cluster file: '+cluster_path)
	url = 'http://'+ambari_address+':'+ambari_port+'/api/v1/clusters/'+cluster_name
	# Check if cluster already exists
	cluster_names = get_cluster_names(ambari_address, ambari_port, username, password)
	if cluster_names:
		if cluster_name in cluster_names:
			return False
		else:
			module.fail_json(msg='Cluster already exists with another name: '+str(cluster_names))
	# Read and post cluster
	cluster_file = open(cluster_path,'r')
	cluster = cluster_file.read()
	req = urllib2.Request(url, data=cluster, headers=get_headers(username,password))
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, error:
		module.fail_json(msg='Failed to build cluster: '+str(error.read()))
	results = json.loads(response.read())
	request_url = results['href']
	#Ambari 2.2.1 bug, must wait for tasks to be issued of build fails
	time.sleep(10)
	if wait_for_build:
		start = time.time()
		while True:
			status,percentage = get_build_status(request_url, username, password)
			if status.lower() == 'completed':
				return True
			elif status.lower() == 'failed':
				module.fail_json(msg='Build has failed after: '+str(time.time() - start)+'s'+
				' with status: '+ status + ' and percent complete: '+str(percentage))
			elif build_timeout != 0 and (time.time() - start) > build_timeout:
				module.fail_json(msg='Build has timed out after: '+str(time.time() - start)+'s'+
				' with status: '+ status + ' and percent complete: '+str(percentage))
	return request_url

def main():
	# Use ansible module to parse arguments
	global module
	module = AnsibleModule(
		argument_spec = dict(
			action=dict(required=True, choices=['post_base_url','wait_for_ambari_api','wait_for_registered_hosts','post_blueprint','get_blueprint_names','get_cluster_names','post_cluster','get_blueprint']),
			path=dict(type='str'),
			blueprint_name=dict(type='str'),
			cluster_name=dict(type='str'),
			stack_version=dict(type='str'),
			stack_services=dict(type='str'),
			hosts=dict(type='str'),
			repo_id=dict(type='str'),
			os_type=dict(type='str'),
			base_url=dict(type='str'),
			ignore_get_error=dict(default=False,type='bool'),
			stack_recommendations=dict(default=False,type='bool'),
			wait_for_build=dict(default=False,type='bool'),
			build_timeout=dict(default=1600,type='int'),
			ambari_address=dict(default='localhost', type='str'),
			ambari_port=dict(default='8080', type='str'),
			username=dict(default='admin', type='str'),
			password=dict(default='admin', type='str')
		)
	)
	if module.params['action'] == 'wait_for_ambari_api':
		wait_for_api(module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'], module.params['password'], module.params['build_timeout'])
		module.exit_json(changed=False, comments='Ambari API up')
	elif module.params['action'] == 'post_base_url':
		for argu in ('stack_version','repo_id','os_type','base_url'):
			if argu not in module.params.keys():
				module.fail_json(msg='You must specify '+argu+' for this action')
		changed = post_base_url(module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],module.params['stack_version'],
			module.params['repo_id'],module.params['os_type'],module.params['base_url'])
		if changed:
			module.exit_json(changed=True, comments='Baseurl posted to Ambari')
		else:
			module.exit_json(changed=False, comments='Baseurl already in Ambari')
	elif module.params['action'] == 'wait_for_registered_hosts':
		if 'hosts' not in module.params.keys():
			module.fail_json(msg='You must specify a host list for this action')
		host_list =  module.params['hosts'].split(',')
		wait_for_registered_hosts(module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'], module.params['password'], host_list, module.params['build_timeout'])
		module.exit_json(changed=False, comments='Hosts registered with Ambari')
	elif module.params['action'] == 'post_blueprint':
		if 'path' not in module.params.keys():
			module.fail_json(msg='You must specify a blueprint file when posting a blueprint')
		if 'blueprint_name' not in module.params.keys():
			module.fail_json(msg='You must specify a blueprint name when posting a blueprint')
		if module.params['stack_recommendations'] and not 'stack_version' in module.params.keys():
			module.fail_json(msg='You must specify a stack_version when using stack recommendations in blueprints')
		if module.params['stack_recommendations'] and not 'hosts' in module.params.keys():
			module.fail_json(msg='You must specify a hosts list when using stack recommendations in blueprints')
		if module.params['stack_recommendations'] and not 'stack_services' in module.params.keys():
			module.fail_json(msg='You must specify a service list when using stack recommendations in blueprints')
		stack_version =  module.params['stack_version'] if module.params['stack_recommendations'] else None
		host_list =  module.params['hosts'].split(',') if module.params['stack_recommendations'] else None
		service_list =  module.params['stack_services'].split(',') if module.params['stack_recommendations'] else None
		changed = post_blueprint(module.params['blueprint_name'],module.params['path'],
			module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],module.params['stack_recommendations'],
			stack_version, host_list, service_list)
		if changed:
			module.exit_json(changed=True, comments='Blueprint posted to Ambari')
		else:
			module.exit_json(changed=False, comments='Blueprint already in Ambari')
	elif module.params['action'] == 'post_cluster':
		if 'path' not in module.params.keys():
			module.fail_json(msg='You must specify a cluster file when posting a blueprint')
		if 'cluster_name' not in module.params.keys():
			module.fail_json(msg='You must specify a cluster name when posting a blueprint')
		changed = post_cluster(module.params['cluster_name'],module.params['path'],
			module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'],
			module.params['wait_for_build'],module.params['build_timeout'])
		if changed and module.params['wait_for_build']:
			module.exit_json(changed=True, comments='Cluster created in Ambari')
		elif changed and not module.params['wait_for_build']:
			module.exit_json(changed=True, comments='Cluster build started, follow: '+str(changed))
		else:
			module.exit_json(changed=False, comments='Cluster already in Ambari')
	elif module.params['action'] == 'get_blueprint_names':
		try:
			names = get_blueprint_names(module.params['ambari_address'],module.params['ambari_port'],
				module.params['username'],module.params['password'])
		except urllib2.URLError, error:
			if module.params['ignore_get_error']:
				module.exit_json(changed=False, comments='Unable to get blueprint names: '+str(error))
			else:
				raise
		module.exit_json(changed=False, comments='Blueprints are: '+','.join(names), ansible_facts={'blueprint_names': names })
	elif module.params['action'] == 'get_cluster_names':
		try:
			names = get_cluster_names(module.params['ambari_address'],module.params['ambari_port'],
				module.params['username'],module.params['password'])
		except urllib2.URLError, error:
			if module.params['ignore_get_error']:
				module.exit_json(changed=False, comments='Unable to get cluster names: '+str(error))
			else:
				raise
		module.exit_json(changed=False, comments='Clusters are: '+','.join(names), ansible_facts={'cluster_names': names })
	elif module.params['action'] == 'get_blueprint':
		if not 'blueprint_name' in module.params.keys():
			module.fail_json(msg='You must specify a blueprint name when getting a blueprint')
		blueprint = get_blueprint(module.params['blueprint_name'],module.params['ambari_address'],module.params['ambari_port'],
			module.params['username'],module.params['password'])
		module.exit_json(changed=False, comments='', ansible_facts={'blueprint': blueprint })
	else:
		module.fail_json(msg='action: '+ module.params['action'] + ' is not defined.')

# import module snippets
from ansible.module_utils.basic import *
main()