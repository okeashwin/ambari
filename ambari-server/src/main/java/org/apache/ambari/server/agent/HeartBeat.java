/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.ambari.server.agent;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlType;

/**
 *
 *
 * Data model for Ambari Agent to send heartbeat to Ambari Server.
 *
 */
@XmlRootElement
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "", propOrder = {})
public class HeartBeat {
  @XmlElement
  private long responseId = -1;
  @XmlElement
  private long timestamp;
  @XmlElement
  private String hostname;
  @XmlElement
  List<CommandReport> reports = new ArrayList<CommandReport>();
  @XmlElement
  List<ComponentStatus> componentStatus = new ArrayList<ComponentStatus>();
  @XmlElement
  HostStatus nodeStatus;

  public long getResponseId() {
    return responseId;
  }

  public void setResponseId(long responseId) {
    this.responseId=responseId;
  }

  public long getTimestamp() {
    return timestamp;
  }

  public String getHostname() {
    return hostname;
  }

  public void setTimestamp(long timestamp) {
    this.timestamp = timestamp;
  }

  public void setHostname(String hostname) {
    this.hostname = hostname;
  }

  public List<CommandReport> getCommandReports() {
    return this.reports;
  }

  public HostStatus getNodeStatus() {
    return nodeStatus;
  }

  public void setNodeStatus(HostStatus nodeStatus) {
    this.nodeStatus = nodeStatus;
  }
}
