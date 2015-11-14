/*
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

package org.apache.ambari.server.api;

import com.google.gson.Gson;
import com.google.inject.Inject;
import com.google.inject.name.Named;
import org.eclipse.jetty.http.HttpStatus;
import org.eclipse.jetty.http.MimeTypes;
/*

Code being commented out for a test migration to Jetty 9

import org.eclipse.jetty.server.AbstractHttpConnection;
*/
import org.eclipse.jetty.server.HttpConnection;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.handler.ErrorHandler;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

public class AmbariErrorHandler extends ErrorHandler{
  private final Gson gson;

  @Inject
  public AmbariErrorHandler(@Named("prettyGson") Gson prettyGson) {
    this.gson = prettyGson;
  }

  @Override
  public void handle(String target, Request baseRequest, HttpServletRequest request, HttpServletResponse response) throws IOException {
    /*

    Code being commented out for a test migration to Jetty 9

    AbstractHttpConnection connection = AbstractHttpConnection.getCurrentConnection();
    connection.getRequest().setHandled(true);

    */

    HttpConnection connection = HttpConnection.getCurrentConnection();
    connection.getHttpChannel().getRequest().setHandled(true);


    /*

    Code being commented out for a test migration to Jetty 9

    response.setContentType(MimeTypes.TEXT_PLAIN);
    */

    response.setContentType(String.valueOf(MimeTypes.Type.TEXT_PLAIN));

    Map<String, Object> errorMap = new LinkedHashMap<String, Object>();

    /*
    Code being commented out for a test migration to Jetty 9

    int code = connection.getResponse().getStatus();
    */

    int code = connection.getHttpChannel().getResponse().getStatus();
    errorMap.put("status", code);

    /*
    Code being commented out for a test migration to Jetty 9

    String message = connection.getResponse().getReason();
    */


    String message = connection.getHttpChannel().getResponse().getReason();
    if (message == null) {
      message = HttpStatus.getMessage(code);
    }
    errorMap.put("message", message);

    gson.toJson(errorMap, response.getWriter());
  }
}
