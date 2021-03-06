#!/usr/bin/env python
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

"""

from resource_management.core.exceptions import Fail
from resource_management.core.resources.service import ServiceConfig
from resource_management.core.resources.system import Directory, Execute, File, Link
from resource_management.core.source import InlineTemplate
from resource_management.libraries.resources.template_config import TemplateConfig
from resource_management.libraries.functions.format import format
from resource_management.libraries.script.script import Script
from resource_management.core.source import Template
from resource_management.libraries.functions import compare_versions
from storm_yaml_utils import yaml_config_template, yaml_config
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl
from ambari_commons import OSConst

@OsFamilyFuncImpl(os_family=OSConst.WINSRV_FAMILY)
def storm(name=None):
  import params
  yaml_config("storm.yaml",
              conf_dir=params.conf_dir,
              configurations=params.config['configurations']['storm-site'],
              owner=params.storm_user
  )

  if params.service_map.has_key(name):
    service_name = params.service_map[name]
    ServiceConfig(service_name,
                  action="change_user",
                  username = params.storm_user,
                  password = Script.get_password(params.storm_user))


@OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
def storm(name=None):
  import params

  Directory(params.log_dir,
            owner=params.storm_user,
            group=params.user_group,
            mode=0777,
            recursive=True
  )

  Directory([params.pid_dir, params.local_dir],
            owner=params.storm_user,
            group=params.user_group,
            recursive=True,
            cd_access="a",
  )

  Directory(params.conf_dir,
            group=params.user_group,
            recursive=True,
            cd_access="a",
  )

  File(format("{conf_dir}/config.yaml"),
       content=Template("config.yaml.j2"),
       owner=params.storm_user,
       group=params.user_group
  )

  configurations = params.config['configurations']['storm-site']

  File(format("{conf_dir}/storm.yaml"),
       content=yaml_config_template(configurations),
       owner=params.storm_user,
       group=params.user_group
  )

  if params.has_metric_collector:
    File(format("{conf_dir}/storm-metrics2.properties"),
        owner=params.storm_user,
        group=params.user_group,
        content=Template("storm-metrics2.properties.j2")
    )

    # Remove symlink. It can be there, if you doing upgrade from HDP < 2.2 to HDP >= 2.2
    Link("/usr/lib/storm/lib/ambari-metrics-storm-sink.jar",
         action="delete")

    Execute(format("{sudo} ln -s {metric_collector_sink_jar} {storm_lib_dir}/ambari-metrics-storm-sink.jar"),
            not_if=format("ls {storm_lib_dir}/ambari-metrics-storm-sink.jar"),
            only_if=format("ls {metric_collector_sink_jar}")
    )

  File(format("{conf_dir}/storm-env.sh"),
    owner=params.storm_user,
    content=InlineTemplate(params.storm_env_sh_template)
  )
  
  if params.storm_logs_supported:
    File(format("{log4j_dir}/cluster.xml"),
      owner=params.storm_user,
      content=InlineTemplate(params.storm_cluster_log4j_content)
    )
    File(format("{log4j_dir}/worker.xml"),
      owner=params.storm_user,
      content=InlineTemplate(params.storm_worker_log4j_content)
    )
  
  if params.security_enabled:
    TemplateConfig(format("{conf_dir}/storm_jaas.conf"),
                   owner=params.storm_user
    )
    if params.hdp_stack_version != "" and compare_versions(params.hdp_stack_version, '2.2') >= 0:
      TemplateConfig(format("{conf_dir}/client_jaas.conf"),
                     owner=params.storm_user
      )
      minRuid = configurations['_storm.min.ruid'] if configurations.has_key('_storm.min.ruid') else ''
      
      min_user_ruid = int(minRuid) if minRuid.isdigit() else _find_real_user_min_uid()
      
      File(format("{conf_dir}/worker-launcher.cfg"),
           content=Template("worker-launcher.cfg.j2", min_user_ruid = min_user_ruid),
           owner='root',
           group=params.user_group
      )


'''
Finds minimal real user UID
'''
def _find_real_user_min_uid():
  with open('/etc/login.defs') as f:
    for line in f:
      if line.strip().startswith('UID_MIN') and len(line.split()) == 2 and line.split()[1].isdigit():
        return int(line.split()[1])
  raise Fail("Unable to find UID_MIN in file /etc/login.defs. Expecting format e.g.: 'UID_MIN    500'")  
