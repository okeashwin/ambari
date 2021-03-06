/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * <p/>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p/>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.ambari.server.controller.metrics.timeline.cache;

import net.sf.ehcache.pool.sizeof.ReflectionSizeOf;
import net.sf.ehcache.pool.sizeof.SizeOf;
import org.apache.ambari.server.controller.internal.TemporalInfoImpl;
import org.apache.ambari.server.controller.spi.TemporalInfo;
import org.apache.hadoop.metrics2.sink.timeline.TimelineMetric;
import org.junit.Assert;
import org.junit.Test;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

public class TimelineMetricCacheSizingTest {

  SizeOf reflectionSizeOf = new ReflectionSizeOf();

  private TimelineMetric getSampleTimelineMetric(String metricName) {
    TimelineMetric metric = new TimelineMetric();
    metric.setMetricName(metricName);
    metric.setAppId("KAFKA_BROKER");
    metric.setInstanceId("NULL");
    metric.setHostName("my.privatehostname.of.average.length");
    metric.setTimestamp(System.currentTimeMillis());
    metric.setStartTime(System.currentTimeMillis());
    metric.setType("LONG");

    // JSON dser gives a LinkedHashMap
    TreeMap<Long, Double> valueMap = new TreeMap<>();
    long now = System.currentTimeMillis();
    for (int i = 0; i < 25000; i++) {
      valueMap.put(new Long(now + i), new Double(1.0 + i));
    }

    metric.setMetricValues(valueMap);

    return metric;
  }

  @Test
  public void testTimelineMetricCacheSizing() throws Exception {
    Set<String> metricNames = new HashSet<>();
    String metric1 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName1";
    String metric2 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName2";
    String metric3 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName3";
    String metric4 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName4";
    String metric5 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName5";
    String metric6 = "prefix1.suffix1.suffix2.actualNamePrefix.longMetricName6";

    metricNames.add(metric1);
    metricNames.add(metric2);
    metricNames.add(metric3);
    metricNames.add(metric4);
    metricNames.add(metric5);
    metricNames.add(metric6);

    long now = System.currentTimeMillis();
    TemporalInfo temporalInfo = new TemporalInfoImpl(now - 1000, now, 15);

    TimelineAppMetricCacheKey key = new TimelineAppMetricCacheKey(
      metricNames, "KAFKA_BROKER", temporalInfo);
    // Some random spec
    key.setSpec("http://104.196.94.129:6188/ws/v1/timeline/metrics?metricNames=" +
      "jvm.JvmMetrics.MemHeapCommittedM&appId=RESOURCEMANAGER&" +
      "startTime=1439522640000&endTime=1440127440000&precision=hours");

    Map<String, TimelineMetric> metricMap = new HashMap<>();
    metricMap.put(metric1, getSampleTimelineMetric(metric1));
    metricMap.put(metric2, getSampleTimelineMetric(metric2));
    metricMap.put(metric3, getSampleTimelineMetric(metric3));
    metricMap.put(metric4, getSampleTimelineMetric(metric4));
    metricMap.put(metric5, getSampleTimelineMetric(metric5));
    metricMap.put(metric6, getSampleTimelineMetric(metric6));

    TimelineMetricsCacheValue value = new TimelineMetricsCacheValue(now -
      1000, now, metricMap, null);

    TimelineMetricsCacheSizeOfEngine customSizeOfEngine = new TimelineMetricsCacheSizeOfEngine();

    long bytesFromReflectionEngine =
      reflectionSizeOf.deepSizeOf(1000, false, key).getCalculated() +
      reflectionSizeOf.deepSizeOf(1000, false, value).getCalculated();

    long bytesFromCustomSizeOfEngine = customSizeOfEngine.sizeOf(key, value, null).getCalculated();

    long sampleSizeInMB = bytesFromReflectionEngine / (1024 * 1024);
    long discrepancyInKB = Math.abs(bytesFromCustomSizeOfEngine - bytesFromReflectionEngine) / 1024;

    Assert.assertTrue("Sample size is greater that 10 MB", sampleSizeInMB > 10);
    Assert.assertTrue("Discrepancy in values is less than 10K", discrepancyInKB  < 10);
  }
}
