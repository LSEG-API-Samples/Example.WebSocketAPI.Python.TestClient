#|-----------------------------------------------------------------------------
#|            This source code is provided under the Apache 2.0 license      --
#|  and is provided AS IS with no warranty or guarantee of fit for purpose.  --
#|                See the project's LICENSE.md for details.                  --
#|           Copyright Refinitiv 2019. All rights reserved.                  --
#|-----------------------------------------------------------------------------

#!/usr/bin/env python
""" Example of requesting Reuters domain Models using Websockets with Views / Streaming / Snapshot """

import sys
import time
import getopt
import socket
import json
import websocket
import threading
from threading import Thread, Event
from collections import defaultdict

# Global Default Variables for connection
hostname = 'localhost'      # Data server 
port = '15000'              # Data server port
ping_timeout_interval = 30  # How often do we expect to recieve Ping from server
ping_timeout_time = 0       # If not received a Ping by this time then timeout and exit
start_time = 0              # Time when first Market Data request made

# Other Global default variables
user = 'user'       # Default username for ADS login
app_id = '256'      # Default application ID for login
position = socket.gethostbyname(socket.gethostname())
simpleRicList = []    # List of RICs to request
domainRicList =[]   # List of RICs with Domain specified
viewList = []   # List of Fields (FIDs or Names) to use in View Request
domainModel = None  # Websocket interface defaults to MarketPrice if not specified
serviceName = None  # EDP or ADS typically has a default service configured
snapshot = False    # Make Snapshot request (rather than the default streaming)
dumpRcvd = False    # Dump messages received from server
dumpPP = False      # Dump the incoming Ping and outgoing Pong messages
dumpSent = False    # Dump out the Requests to the SENT to the server
dumpStatus = False  # Dump out any Status Msgs received from server
autoExit = False    # Exit once Refresh (or Status closed) received for all requests

reqCnt = 0      # Number of Data Items requested
imgCnt = 0      # Data Refresh messages received
updCnt = 0      # Update messages received
statusCnt = 0   # Status messages received
pingCnt = 0     # Ping messages (= Pongs sent)
closedCnt = 0   # Specifically Closed status message (e.g. item not found)
logged_in = False # Did we get a successful Login response yet

auth_token = None       # Autorization token for EDP connections
web_socket_app = None   
web_socket_open = False
shutdown_app = False    # flag to indicate shutdown
edp_mode = False        # Are connecting to EDP

# Dump some basic stats to console
def print_stats():
    global imgCnt, updCnt, statusCnt, pingCnt, start_time
    elapsed = 0
    if (start_time!=0):
        elapsed = time.time() - start_time
    print("Stats; Refresh: {} \tUpdates: {} \tStatus: {} \tPings: {} \tElapsed Time: {:.2f}secs"
        .format(imgCnt,updCnt,statusCnt,pingCnt, elapsed))

# Various Login related parameters
def set_Login(u,a,p,t,e):
    global user, app_id, position, auth_token, edp_mode
    app_id=a
    user=u
    position=p
    auth_token=t
    edp_mode=e

# Data request related parameters
def set_Request_Attr(service,rList,rdm,snap, dmList):
    global simpleRicList,domainModel,snapshot, domainRicList, serviceName
    serviceName=service
    simpleRicList=rList
    domainModel=rdm
    snapshot=snap
    domainRicList=dmList

# View used to request Field filtering by the server
def set_viewList(vList):
    global viewList
    viewList=vList
    #print("Set viewList to", viewList, "from", vList)

# Attempt clean shutdown
def cleanup(ws):
    global shutdown_app
    send_login_close(ws)
    shutdown_app=True   # signal to main loop to exit
    #ws.close()     # Cannot use due to Websocket client issue/bug

# Call this each time we send or receive a message 
# to reset the timeout for the next ping
def reset_ping_time():          
    global ping_timeout_time    
    ping_timeout_time = time.time() + ping_timeout_interval

# Has it been too long since last ping
def ping_timedout():    
    if (ping_timeout_time > 0) and (time.time() > ping_timeout_time):
        print("No ping from server, timing out")
        return True

# Process the JSON message received from server
def process_message(ws, message_json):
    global imgCnt, updCnt, statusCnt, pingCnt, closedCnt,shutdown_app

    # Get Message Type
    message_type = message_json['Type']

    message_domain = "MarketPrice"  # Dont get Domain in MarketPrice message
    if 'Domain' in message_json:
        message_domain = message_json['Domain']

    # Process different Message Types
    if message_type == "Refresh":
        if message_domain == "Login":
            process_login_response(ws, message_json)
        else:   
            if not (('Complete' in message_json) and    # Default value for Complete is True
                (message_json['Complete']==False)) :    # Only count Refresh If 'Complete' not present or present as True
                imgCnt += 1     # Only for Data related Refresh i.e. not Login
    elif message_type == "Update":
        updCnt += 1
    elif message_type == "Status":
        # Count Data Item Status msg received
        if message_domain != "Login":
            statusCnt += 1
            stream_state = message_json['State']['Stream']
            data_state = message_json['State']['Data']
            # Was the item request rejected by server & stream Closed?
            if stream_state=='Closed' and data_state=='Suspect':
                closedCnt += 1
            if dumpStatus and not dumpRcvd:     # if dumpRCVD set then Status will be dumped elsewhere
                print(json.dumps(message_json))
        else:
            print("LOGIN STATUS:")      # Login status usually a problem - so report it and return
            print(json.dumps(message_json, sort_keys=True, indent=2, separators=(',', ':')))
            if message_json['State']['Stream'] != "Open" or message_json['State']['Data'] != "Ok":
                print("Login Request rejected / failed.")
                shutdown_app=True
        return
    
    elif message_type == "Ping":    # If we get a Ping from the Server
        pingCnt += 1                # we need to respond with a Pong 
        pong_json = { 'Type':'Pong' }
        ws.send(json.dumps(pong_json))
        if (dumpPP):
            print("RCVD:", json.dumps(message_json),
                    " SENT:", json.dumps(pong_json))

    elif message_type == 'Error':   # Oh Dear - server did not like our Request
        print("ERR: ")
        print(json.dumps(message_json, sort_keys=True, indent=2, separators=(',', ':')))
        cleanup(ws)

    # Cleanup and exit - if autoExit and we have received response to all requests
    if (autoExit and (reqCnt==imgCnt+closedCnt)):
        cleanup(ws)

# We received a Login Refresh Response from Server - success!
def process_login_response(ws, message_json):
    
    global ping_timeout_interval, start_time, logged_in

    logged_in = True

    # Get Ping timeout interval supplied by server
    ping_timeout_interval = int(message_json['Elements']['PingTimeout'])

    # Get the Login StreamID and increment - ready for Data request
    next_stream_id = int(message_json['ID']) + 1

    # For statistics - we start timing after Login 
    # and just before we send our data requests
    start_time = time.time()
    """ Send item request """
    if (domainRicList):
        send_multi_domain_data_request(ws, next_stream_id)
    else:
        send_single_domain_data_request(ws, domainModel, simpleRicList, next_stream_id)

# User specified '-ef' and file with multiple domain types
# So we need to group RICs by Domain and make a batch request for each group
def send_multi_domain_data_request(ws, streamID):

    """ Group Market Data request by Domain type """
    """ and then make batch request for each group """
    grouped = defaultdict(list)
    # Create lists grouped by Domain Type
    for domain, ric in domainRicList:
        grouped[domain].append(ric)
    
    #print(grouped)

    # For each Domain type group, call the data request method
    for i, (domain, rics) in enumerate(grouped.items()):
        send_single_domain_data_request(ws, domain, rics, i + streamID)
        # Server allocates unique StreamID to each item in a Batch
        # so we need to increment StreamID appropriately for next request
        streamID += len(rics)   


# Make a Batch request for all the RICs in ricList 
# with any specified Views and Domains etc. 
def send_single_domain_data_request(ws, domain, ricList, streamID):
    global reqCnt
    """ Create and send Market Data request for a single Domain type"""
    
    # increment the data items requested count
    reqCnt += len(ricList)

    mp_req_json = {
        'ID': streamID,
        'Key': {
            'Name': ricList,
        },
    }

    # If user specified a service add it to the request
    # otherwise server will use any server configured default 
    if serviceName:
        mp_req_json['Key']['Service'] = serviceName

    # If user specified a view and/or domain add them to the request
    if (len(viewList)>0):
        mp_req_json['View'] = viewList
    if (domain!=None):
        mp_req_json['Domain'] = domain
    
    # Did user specify Snapshot Mode - if so override Streaming default of True
    if snapshot:
        mp_req_json['Streaming'] = False

    # Send the Data request to the server
    ws.send(json.dumps(mp_req_json))
    if (dumpSent):
        print("SENT MP Request:")
        print(json.dumps(mp_req_json, sort_keys=True, indent=2, separators=(',', ':')))

# Refreshed auth token so send login request again
def reissue_token(ws, token):
    global auth_token
    auth_token = token
    send_login_request(ws, True)

# Send a Login request - for ADS or EDP
def send_login_request(ws, is_refresh_token=False):
    """ Generate a login request from command line data (or defaults) and send """
    
    # Set common values for EDP and ADS login
    # Note StreamID is 1
    login_json = {
        'ID': 1,
        'Domain': 'Login',
        'Key': {
            'Elements': {
                'ApplicationId': '',
                'Position': ''
            }
        }
    }
    login_json['Key']['Elements']['ApplicationId'] = app_id
    login_json['Key']['Elements']['Position'] = position

    # EDP login request authentication token / ADS requires username
    if (edp_mode):  # Connected to EDP
        login_json['Key']['NameType'] = 'AuthnToken'
        login_json['Key']['Elements']['AuthenticationToken'] = auth_token
        # If the auth token is a refresh token, this is not our first login attempt.
        if is_refresh_token:
            login_json['Refresh'] = False
    else:   # TREP ADS connection
        login_json['Key']['Name'] = user
    
    ws.send(json.dumps(login_json))
    if (dumpSent):
        print("SENT Login Request:")
        print(json.dumps(login_json, sort_keys=True, indent=2, separators=(',', ':')))

# Send a Logout request to server - with StreamID 1
def send_login_close(ws):
    logout_json = {
        'Domain': 'Login',
        'ID': 1,
        'Type': 'Close'
    }
    ws.send(json.dumps(logout_json))
    if (dumpSent):
        print("SENT Logout Request:")
        print(json.dumps(logout_json, sort_keys=True, indent=2, separators=(',', ':')))

# Received a JSON message payload from server
def on_message(ws, message):
    """ Called when message received, parse message into JSON for processing """
    message_json = json.loads(message)
    if dumpRcvd:
        print("RCVD: ")
        print(json.dumps(message_json, sort_keys=True, indent=2, separators=(',', ':')))

    # extract and process individual messages
    for singleMsg in message_json:
        process_message(ws, singleMsg)
    # We have received a message from server - so reset the Ping timeout
    reset_ping_time()

def on_error(ws, error):
    """ Called when websocket error has occurred """
    print(error)


def on_close(ws):
    """ Called when websocket is closed """
    global web_socket_open, shutdown_app
    print("WebSocket Closed")
    web_socket_open = False
    shutdown_app = True

def on_open(ws):
    """ Called when handshake is complete and websocket is open, send login """

    print("WebSocket successfully connected!")
    print_stats()
    global web_socket_open
    web_socket_open = True
    reset_ping_time()
    send_login_request(ws)


