"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Ambari Agent

"""
import os

from resource_management.libraries.script.script import Script
from resource_management.libraries.resources.hdfs_resource import HdfsResource
from resource_management.libraries.functions import conf_select
from resource_management.libraries.functions import hdp_select
from resource_management.libraries.functions import format
from resource_management.libraries.functions import get_kinit_path
from resource_management.libraries.functions.version import format_hdp_stack_version
from resource_management.libraries.functions.default import default
from resource_management.libraries import functions

import status_params

# a map of the Ambari role to the component name
# for use with /usr/hdp/current/<component>
MAPR_SERVER_ROLE_DIRECTORY_MAP = {
  'HISTORYSERVER' : 'hadoop-mapreduce-historyserver',
  'MAPREDUCE2_CLIENT' : 'hadoop-mapreduce-client',
}

YARN_SERVER_ROLE_DIRECTORY_MAP = {
  'APP_TIMELINE_SERVER' : 'hadoop-yarn-timelineserver',
  'NODEMANAGER' : 'hadoop-yarn-nodemanager',
  'RESOURCEMANAGER' : 'hadoop-yarn-resourcemanager',
  'YARN_CLIENT' : 'hadoop-yarn-client'
}

# server configurations
config = Script.get_config()
tmp_dir = Script.get_tmp_dir()

stack_name = default("/hostLevelParams/stack_name", None)

# This is expected to be of the form #.#.#.#
stack_version_unformatted = str(config['hostLevelParams']['stack_version'])
hdp_stack_version_major = format_hdp_stack_version(stack_version_unformatted)
hdp_stack_version = functions.get_hdp_version('hadoop-yarn-resourcemanager')

# New Cluster Stack Version that is defined during the RESTART of a Stack Upgrade.
# It cannot be used during the initial Cluser Install because the version is not yet known.
version = default("/commandParams/version", None)

hostname = config['hostname']

# hadoop default parameters
hadoop_libexec_dir = hdp_select.get_hadoop_dir("libexec")
hadoop_bin = hdp_select.get_hadoop_dir("sbin")
hadoop_bin_dir = hdp_select.get_hadoop_dir("bin")
hadoop_conf_dir = conf_select.get_hadoop_conf_dir()
hadoop_yarn_home = '/usr/lib/hadoop-yarn'
hadoop_mapred2_jar_location = "/usr/lib/hadoop-mapreduce"
mapred_bin = "/usr/lib/hadoop-mapreduce/sbin"
yarn_bin = "/usr/lib/hadoop-yarn/sbin"
yarn_container_bin = "/usr/lib/hadoop-yarn/bin"
hadoop_java_io_tmpdir = os.path.join(tmp_dir, "hadoop_java_io_tmpdir")

# hadoop parameters for 2.2+
if Script.is_hdp_stack_greater_or_equal("2.2"):
  # MapR directory root
  mapred_role_root = "hadoop-mapreduce-client"
  command_role = default("/role", "")
  if command_role in MAPR_SERVER_ROLE_DIRECTORY_MAP:
    mapred_role_root = MAPR_SERVER_ROLE_DIRECTORY_MAP[command_role]

  # YARN directory root
  yarn_role_root = "hadoop-yarn-client"
  if command_role in YARN_SERVER_ROLE_DIRECTORY_MAP:
    yarn_role_root = YARN_SERVER_ROLE_DIRECTORY_MAP[command_role]

  hadoop_mapred2_jar_location = format("/usr/hdp/current/{mapred_role_root}")
  mapred_bin = format("/usr/hdp/current/{mapred_role_root}/sbin")

  hadoop_yarn_home = format("/usr/hdp/current/{yarn_role_root}")
  yarn_bin = format("/usr/hdp/current/{yarn_role_root}/sbin")
  yarn_container_bin = format("/usr/hdp/current/{yarn_role_root}/bin")

  # Timeline Service property that was added in 2.2
  ats_leveldb_state_store_dir = config['configurations']['yarn-site']['yarn.timeline-service.leveldb-state-store.path']

hadoop_conf_secure_dir = os.path.join(hadoop_conf_dir, "secure")

limits_conf_dir = "/etc/security/limits.d"
yarn_user_nofile_limit = default("/configurations/yarn-env/yarn_user_nofile_limit", "32768")
yarn_user_nproc_limit = default("/configurations/yarn-env/yarn_user_nproc_limit", "65536")

mapred_user_nofile_limit = default("/configurations/mapred-env/mapred_user_nofile_limit", "32768")
mapred_user_nproc_limit = default("/configurations/mapred-env/mapred_user_nproc_limit", "65536")

execute_path = os.environ['PATH'] + os.pathsep + hadoop_bin_dir + os.pathsep + yarn_container_bin

ulimit_cmd = "ulimit -c unlimited;"

mapred_user = status_params.mapred_user
yarn_user = status_params.yarn_user
hdfs_user = config['configurations']['hadoop-env']['hdfs_user']

smokeuser = config['configurations']['cluster-env']['smokeuser']
smokeuser_principal = config['configurations']['cluster-env']['smokeuser_principal_name']
security_enabled = config['configurations']['cluster-env']['security_enabled']
nm_security_marker = '/var/lib/hadoop-yarn/nm_security_enabled'
current_nm_security_state = os.path.isfile(nm_security_marker)
toggle_nm_security = (current_nm_security_state and not security_enabled) or (not current_nm_security_state and security_enabled)
rm_security_marker = "/var/lib/hadoop-yarn/rm_security_enabled"
current_rm_security_state = os.path.isfile(rm_security_marker)
toggle_rm_security = (current_rm_security_state and not security_enabled) or (not current_rm_security_state and security_enabled)
smoke_user_keytab = config['configurations']['cluster-env']['smokeuser_keytab']
yarn_executor_container_group = config['configurations']['yarn-site']['yarn.nodemanager.linux-container-executor.group']
yarn_nodemanager_container_executor_class =  config['configurations']['yarn-site']['yarn.nodemanager.container-executor.class']
is_linux_container_executor = (yarn_nodemanager_container_executor_class == 'org.apache.hadoop.yarn.server.nodemanager.LinuxContainerExecutor')
container_executor_mode = 06050 if is_linux_container_executor else 02050
kinit_path_local = get_kinit_path(default('/configurations/kerberos-env/executable_search_paths', None))
rm_hosts = config['clusterHostInfo']['rm_host']
rm_host = rm_hosts[0]
rm_port = config['configurations']['yarn-site']['yarn.resourcemanager.webapp.address'].split(':')[-1]
rm_https_port = config['configurations']['yarn-site']['yarn.resourcemanager.webapp.https.address'].split(':')[-1]
# TODO UPGRADE default, update site during upgrade
rm_nodes_exclude_path = default("/configurations/yarn-site/yarn.resourcemanager.nodes.exclude-path","/etc/hadoop/conf/yarn.exclude")

java64_home = config['hostLevelParams']['java_home']
hadoop_ssl_enabled = default("/configurations/core-site/hadoop.ssl.enabled", False)

yarn_heapsize = config['configurations']['yarn-env']['yarn_heapsize']
resourcemanager_heapsize = config['configurations']['yarn-env']['resourcemanager_heapsize']
nodemanager_heapsize = config['configurations']['yarn-env']['nodemanager_heapsize']
apptimelineserver_heapsize = default("/configurations/yarn-env/apptimelineserver_heapsize", 1024)
ats_leveldb_dir = config['configurations']['yarn-site']['yarn.timeline-service.leveldb-timeline-store.path']
yarn_log_dir_prefix = config['configurations']['yarn-env']['yarn_log_dir_prefix']
yarn_pid_dir_prefix = status_params.yarn_pid_dir_prefix
mapred_pid_dir_prefix = status_params.mapred_pid_dir_prefix
mapred_log_dir_prefix = config['configurations']['mapred-env']['mapred_log_dir_prefix']
mapred_env_sh_template = config['configurations']['mapred-env']['content']
yarn_env_sh_template = config['configurations']['yarn-env']['content']
yarn_nodemanager_recovery_dir = default('/configurations/yarn-site/yarn.nodemanager.recovery.dir', None)

if len(rm_hosts) > 1:
  additional_rm_host = rm_hosts[1]
  rm_webui_address = format("{rm_host}:{rm_port},{additional_rm_host}:{rm_port}")
  rm_webui_https_address = format("{rm_host}:{rm_https_port},{additional_rm_host}:{rm_https_port}")
else:
  rm_webui_address = format("{rm_host}:{rm_port}")
  rm_webui_https_address = format("{rm_host}:{rm_https_port}")

nm_webui_address = config['configurations']['yarn-site']['yarn.nodemanager.webapp.address']
hs_webui_address = config['configurations']['mapred-site']['mapreduce.jobhistory.webapp.address']
nm_address = config['configurations']['yarn-site']['yarn.nodemanager.address']  # still contains 0.0.0.0
if hostname and nm_address and nm_address.startswith("0.0.0.0:"):
  nm_address = nm_address.replace("0.0.0.0", hostname)

nm_local_dirs = config['configurations']['yarn-site']['yarn.nodemanager.local-dirs']
nm_log_dirs = config['configurations']['yarn-site']['yarn.nodemanager.log-dirs']

nm_local_dirs_list = nm_local_dirs.split(',')
nm_log_dirs_list = nm_log_dirs.split(',')

distrAppJarName = "hadoop-yarn-applications-distributedshell-2.*.jar"
hadoopMapredExamplesJarName = "hadoop-mapreduce-examples-2.*.jar"

yarn_pid_dir = status_params.yarn_pid_dir
mapred_pid_dir = status_params.mapred_pid_dir

mapred_log_dir = format("{mapred_log_dir_prefix}/{mapred_user}")
yarn_log_dir = format("{yarn_log_dir_prefix}/{yarn_user}")
mapred_job_summary_log = format("{mapred_log_dir_prefix}/{mapred_user}/hadoop-mapreduce.jobsummary.log")
yarn_job_summary_log = format("{yarn_log_dir_prefix}/{yarn_user}/hadoop-mapreduce.jobsummary.log")

user_group = config['configurations']['cluster-env']['user_group']

#exclude file
exclude_hosts = default("/clusterHostInfo/decom_nm_hosts", [])
exclude_file_path = default("/configurations/yarn-site/yarn.resourcemanager.nodes.exclude-path","/etc/hadoop/conf/yarn.exclude")

ats_host = set(default("/clusterHostInfo/app_timeline_server_hosts", []))
has_ats = not len(ats_host) == 0

nm_hosts = default("/clusterHostInfo/nm_hosts", [])

# don't using len(nm_hosts) here, because check can take too much time on large clusters
number_of_nm = 1

# default kinit commands
rm_kinit_cmd = ""
yarn_timelineservice_kinit_cmd = ""
nodemanager_kinit_cmd = ""

if security_enabled:
  _rm_principal_name = config['configurations']['yarn-site']['yarn.resourcemanager.principal']
  _rm_principal_name = _rm_principal_name.replace('_HOST',hostname.lower())
  _rm_keytab = config['configurations']['yarn-site']['yarn.resourcemanager.keytab']
  rm_kinit_cmd = format("{kinit_path_local} -kt {_rm_keytab} {_rm_principal_name};")

  # YARN timeline security options are only available in HDP Champlain
  if has_ats:
    _yarn_timelineservice_principal_name = config['configurations']['yarn-site']['yarn.timeline-service.principal']
    _yarn_timelineservice_principal_name = _yarn_timelineservice_principal_name.replace('_HOST', hostname.lower())
    _yarn_timelineservice_keytab = config['configurations']['yarn-site']['yarn.timeline-service.keytab']
    yarn_timelineservice_kinit_cmd = format("{kinit_path_local} -kt {_yarn_timelineservice_keytab} {_yarn_timelineservice_principal_name};")

  if 'yarn.nodemanager.principal' in config['configurations']['yarn-site']:
    _nodemanager_principal_name = default('/configurations/yarn-site/yarn.nodemanager.principal', None)
    if _nodemanager_principal_name:
      _nodemanager_principal_name = _nodemanager_principal_name.replace('_HOST', hostname.lower())

    _nodemanager_keytab = config['configurations']['yarn-site']['yarn.nodemanager.keytab']
    nodemanager_kinit_cmd = format("{kinit_path_local} -kt {_nodemanager_keytab} {_nodemanager_principal_name};")


yarn_log_aggregation_enabled = config['configurations']['yarn-site']['yarn.log-aggregation-enable']
yarn_nm_app_log_dir =  config['configurations']['yarn-site']['yarn.nodemanager.remote-app-log-dir']
mapreduce_jobhistory_intermediate_done_dir = config['configurations']['mapred-site']['mapreduce.jobhistory.intermediate-done-dir']
mapreduce_jobhistory_done_dir = config['configurations']['mapred-site']['mapreduce.jobhistory.done-dir']
jobhistory_heapsize = default("/configurations/mapred-env/jobhistory_heapsize", "900")
jhs_leveldb_state_store_dir = default('/configurations/mapred-site/mapreduce.jobhistory.recovery.store.leveldb.path', "/hadoop/mapreduce/jhs")

# Tez-related properties
tez_user = config['configurations']['tez-env']['tez_user']

# Tez jars
tez_local_api_jars = '/usr/lib/tez/tez*.jar'
tez_local_lib_jars = '/usr/lib/tez/lib/*.jar'
app_dir_files = {tez_local_api_jars:None}

# Tez libraries
tez_lib_uris = default("/configurations/tez-site/tez.lib.uris", None)

#for create_hdfs_directory
hdfs_user_keytab = config['configurations']['hadoop-env']['hdfs_user_keytab']
hdfs_principal_name = config['configurations']['hadoop-env']['hdfs_principal_name']



hdfs_site = config['configurations']['hdfs-site']
default_fs = config['configurations']['core-site']['fs.defaultFS']

dfs_type = default("/commandParams/dfs_type", "")


import functools
#create partial functions with common arguments for every HdfsResource call
#to create/delete hdfs directory/file/copyfromlocal we need to call params.HdfsResource in code
HdfsResource = functools.partial(
  HdfsResource,
  user=hdfs_user,
  security_enabled = security_enabled,
  keytab = hdfs_user_keytab,
  kinit_path_local = kinit_path_local,
  hadoop_bin_dir = hadoop_bin_dir,
  hadoop_conf_dir = hadoop_conf_dir,
  principal_name = hdfs_principal_name,
  hdfs_site = hdfs_site,
  default_fs = default_fs,
  dfs_type = dfs_type
 )
update_exclude_file_only = default("/commandParams/update_exclude_file_only",False)

mapred_tt_group = default("/configurations/mapred-site/mapreduce.tasktracker.group", user_group)

#taskcontroller.cfg

mapred_local_dir = "/tmp/hadoop-mapred/mapred/local"
hdfs_log_dir_prefix = config['configurations']['hadoop-env']['hdfs_log_dir_prefix']
min_user_id = config['configurations']['yarn-env']['min_user_id']

# Node labels
node_labels_dir = default("/configurations/yarn-site/yarn.node-labels.fs-store.root-dir", None)
node_label_enable = config['configurations']['yarn-site']['yarn.node-labels.enabled']

cgroups_dir = "/cgroups_test/cpu"

# ***********************  RANGER PLUGIN CHANGES ***********************
# ranger host
ranger_admin_hosts = default("/clusterHostInfo/ranger_admin_hosts", [])
has_ranger_admin = not len(ranger_admin_hosts) == 0
xml_configurations_supported = config['configurations']['ranger-env']['xml_configurations_supported']
ambari_server_hostname = config['clusterHostInfo']['ambari_server_host'][0]
# hostname of the active HDFS HA Namenode (only used when HA is enabled)
dfs_ha_namenode_active = default("/configurations/hadoop-env/dfs_ha_initial_namenode_active", None)
if dfs_ha_namenode_active is not None: 
  namenode_hostname = dfs_ha_namenode_active
else:
  namenode_hostname = config['clusterHostInfo']['namenode_host'][0]

ranger_admin_log_dir = default("/configurations/ranger-env/ranger_admin_log_dir","/var/log/ranger/admin")

yarn_http_policy = config['configurations']['yarn-site']['yarn.http.policy']
yarn_https_on = (yarn_http_policy.upper() == 'HTTPS_ONLY')
scheme = 'http' if not yarn_https_on else 'https'
yarn_rm_address = config['configurations']['yarn-site']['yarn.resourcemanager.webapp.address'] if not yarn_https_on else config['configurations']['yarn-site']['yarn.resourcemanager.webapp.https.address']
rm_active_port = rm_https_port if yarn_https_on else rm_port

#ranger yarn properties
if has_ranger_admin:
  is_supported_yarn_ranger = config['configurations']['yarn-env']['is_supported_yarn_ranger']

  if is_supported_yarn_ranger:
    enable_ranger_yarn = (config['configurations']['ranger-yarn-plugin-properties']['ranger-yarn-plugin-enabled'].lower() == 'yes')
    policymgr_mgr_url = config['configurations']['admin-properties']['policymgr_external_url']
    sql_connector_jar = config['configurations']['admin-properties']['SQL_CONNECTOR_JAR']
    xa_audit_db_flavor = (config['configurations']['admin-properties']['DB_FLAVOR']).lower()
    xa_audit_db_name = config['configurations']['admin-properties']['audit_db_name']
    xa_audit_db_user = config['configurations']['admin-properties']['audit_db_user']
    xa_audit_db_password = unicode(config['configurations']['admin-properties']['audit_db_password'])
    xa_db_host = config['configurations']['admin-properties']['db_host']
    repo_name = str(config['clusterName']) + '_yarn'

    ranger_env = config['configurations']['ranger-env']
    ranger_plugin_properties = config['configurations']['ranger-yarn-plugin-properties']
    policy_user = config['configurations']['ranger-yarn-plugin-properties']['policy_user']
    yarn_rest_url = config['configurations']['yarn-site']['yarn.resourcemanager.webapp.address']  

    ranger_plugin_config = {
      'username' : config['configurations']['ranger-yarn-plugin-properties']['REPOSITORY_CONFIG_USERNAME'],
      'password' : unicode(config['configurations']['ranger-yarn-plugin-properties']['REPOSITORY_CONFIG_PASSWORD']),
      'yarn.url' : format('{scheme}://{yarn_rest_url}'),
      'commonNameForCertificate' : config['configurations']['ranger-yarn-plugin-properties']['common.name.for.certificate']
    }

    yarn_ranger_plugin_repo = {
      'isEnabled': 'true',
      'configs': ranger_plugin_config,
      'description': 'yarn repo',
      'name': repo_name,
      'repositoryType': 'yarn',
      'type': 'yarn',
      'assetType': '1'
    }
    #For curl command in ranger plugin to get db connector
    jdk_location = config['hostLevelParams']['jdk_location']
    java_share_dir = '/usr/share/java'
    if xa_audit_db_flavor and xa_audit_db_flavor == 'mysql':
      jdbc_symlink_name = "mysql-jdbc-driver.jar"
      jdbc_jar_name = "mysql-connector-java.jar"
      audit_jdbc_url = format('jdbc:mysql://{xa_db_host}/{xa_audit_db_name}')
      jdbc_driver = "com.mysql.jdbc.Driver"
    elif xa_audit_db_flavor and xa_audit_db_flavor == 'oracle':
      jdbc_jar_name = "ojdbc6.jar"
      jdbc_symlink_name = "oracle-jdbc-driver.jar"
      audit_jdbc_url = format('jdbc:oracle:thin:@//{xa_db_host}')
      jdbc_driver = "oracle.jdbc.OracleDriver"
    elif xa_audit_db_flavor and xa_audit_db_flavor == 'postgres':
      jdbc_jar_name = "postgresql.jar"
      jdbc_symlink_name = "postgres-jdbc-driver.jar"
      audit_jdbc_url = format('jdbc:postgresql://{xa_db_host}/{xa_audit_db_name}')
      jdbc_driver = "org.postgresql.Driver"
    elif xa_audit_db_flavor and xa_audit_db_flavor == 'mssql':
      jdbc_jar_name = "sqljdbc4.jar"
      jdbc_symlink_name = "mssql-jdbc-driver.jar"
      audit_jdbc_url = format('jdbc:sqlserver://{xa_db_host};databaseName={xa_audit_db_name}')
      jdbc_driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
    elif xa_audit_db_flavor and xa_audit_db_flavor == 'sqla':
      jdbc_jar_name = "sajdbc4.jar"
      jdbc_symlink_name = "sqlanywhere-jdbc-driver.tar.gz"
      audit_jdbc_url = format('jdbc:sqlanywhere:database={xa_audit_db_name};host={xa_db_host}')
      jdbc_driver = "sap.jdbc4.sqlanywhere.IDriver"

    downloaded_custom_connector = format("{tmp_dir}/{jdbc_jar_name}")

    driver_curl_source = format("{jdk_location}/{jdbc_symlink_name}")
    driver_curl_target = format("{hadoop_yarn_home}/lib/{jdbc_jar_name}")

    ranger_audit_solr_urls = config['configurations']['ranger-admin-site']['ranger.audit.solr.urls']
    xa_audit_db_is_enabled = config['configurations']['ranger-yarn-audit']['xasecure.audit.destination.db'] if xml_configurations_supported else None
    ssl_keystore_password = unicode(config['configurations']['ranger-yarn-policymgr-ssl']['xasecure.policymgr.clientssl.keystore.password']) if xml_configurations_supported else None
    ssl_truststore_password = unicode(config['configurations']['ranger-yarn-policymgr-ssl']['xasecure.policymgr.clientssl.truststore.password']) if xml_configurations_supported else None
    credential_file = format('/etc/ranger/{repo_name}/cred.jceks') if xml_configurations_supported else None

    #For SQLA explicitly disable audit to DB for Ranger
    if xa_audit_db_flavor == 'sqla':
      xa_audit_db_is_enabled = False
