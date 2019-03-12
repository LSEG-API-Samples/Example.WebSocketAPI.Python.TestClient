#!/usr/bin/env python
#|-----------------------------------------------------------------------------
#|            This source code is provided under the Apache 2.0 license      --
#|  and is provided AS IS with no warranty or guarantee of fit for purpose.  --
#|                See the project's LICENSE.md for details.                  --
#|           Copyright Refinitiv 2019. All rights reserved.                  --
#|-----------------------------------------------------------------------------

import time
import argparse
import sys
import socket
import getpass
import requests
import market_data
import websocket
import json
import threading
from threading import Thread, Event

# Python example that uses the Refinitiv Websocket interface to facilitate the consumption of realtime data.
# This example is meant to be a simplistic version of the 'rmdstestclient' tool and illustrates a variety of scenarios such as:  
#  EDP or ADS connection, Batch / View Request, Streaming / Snapshot, Reuters Domain Models

# Global Variables
simpleRics=None
extRics=None
opts=None
ws_app=None
auth_path = 'auth/oauth2/beta1/token'
sts_token = ''
refresh_token = ''
client_secret = ''
expire_time = 0
scope = 'trapi'
edp_mode = False

# Read RICs from file '-f' option i.e. no domain specified 
# so will be used in conjunction with Domain Model parameter
def readSimpleRicsFile():
    global simpleRics
    try:
        with open(opts.ricFile, 'r') as f:      # Read one RIC per line from file
            simpleRics = [ric.strip(' \t\n\r') for ric in f]  # and strip any whitespace etc
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        return

    print("RICs from file:", simpleRics)

# Read Domain + RIC from multi domain file '-ef' option
# File contains Domain Model Number and RIC seperated by | - one per line e..g
# 6|VOD.L
# 7|BT.L
def readExtRicsFile():
    global extRics
    try:
        with open(opts.ricFileExt, 'r') as f:
            tmpExtRics = f.read().splitlines() # using read.splitlines to strip \n on end of each RIC
        extRics=[]
        for xRic in tmpExtRics:
            tmp = xRic.split("|")
            try:                    # Add entry as Domain number, RIC
                extRics.append((int(tmp[0]), str(tmp[1]).strip(' \t\n\r')))  # strip any whitespaces
            except:pass
        extRics.sort()
        print("SORTED:", extRics)
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        return

    #print("Read {} Multi Domain RICs from file: {}".format(len(extRics), extRics))

# Only one RIC list specifier allowed; -items OR -f OR -ef
def parse_rics():
    global simpleRics
    if (opts.itemList):
        simpleRics = opts.itemList.split(',')
        print(simpleRics)
    elif (opts.ricFile):
        readSimpleRicsFile()
    elif (opts.ricFileExt):
        readExtRicsFile()

def validate_options():
    global opts, edp_mode

    # If password is specified then we are going to attempt EDP connection
    if opts.password:
        # Must have authorisation server specified for EDP connection
        if (not opts.authHostname) or (not opts.authPort):
            print("For EDP connection, Authorisation Host + Port are required")
            return False
        edp_mode = True

    # Dont allow both FIDS and Field Names to be specifed for View request
    if ((opts.viewFIDs) and (opts.viewNames)):  
        print('Only one type of View allowed; -vfids or -vnames')
        return False

    # Ensure only one RIC list /filename specified by user
    ricLists = (opts.itemList, opts.ricFile, opts.ricFileExt)
    ricListCnt=0
    for rics in ricLists:
        if (rics!=None):
            ricListCnt+=1

    if (ricListCnt>1):
        print('Only one RIC list specifier allowed; -items, -f or -ef')
        return False
    elif (not ricListCnt):
        print('Must specify some RICs using one of the following; -items, -f or -ef')
        return False
    else:
        parse_rics()
        # Check if we parsed some RICs to request. 
        if (not simpleRics) and (not extRics):
            print("Was not able to read any RICs from file or command line")
            return False

    # If stats interval is >  specified runtime then reduce interval
    if (opts.exitTimeMins>0) and (opts.statsTimeSecs > (opts.exitTimeMins*60)):
        opts.statsTimeSecs ==  opts.exitTimeMins*60

    # Check if Domain has been specified as a numeric value rather than name
    if opts.domain and opts.domain.isdigit():        
        opts.domain = int(opts.domain)

    return True

# Parge command line arguments
def parse_args(args=None):
    parser = argparse.ArgumentParser(description='python websocket test client',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
                       
    parser.add_argument('-S', dest='service',
                        help='service name to request from',
                        default=None)
    parser.add_argument('-H', dest='host',
                        help='data server hostname / endpoint',
                        default='ads1')
    parser.add_argument('-ah', dest='authHostname',
                        help='authorization server hostname',
                        default='api.edp.thomsonreuters.com')
    parser.add_argument('-p', dest='port',
                        help='port of the server',
                        type=int,
                        default=15000)
    parser.add_argument('-ap', dest='authPort',
                        help='port of the authorisation server',
                        type=int,
                        default=443)
    parser.add_argument('-u', dest='user',
                        help='login user name',
                        default=getpass.getuser())
    parser.add_argument('-pw', dest='password',
                        help='EDP user password')
    parser.add_argument('-pos', dest='position',
                        help='application position',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-aid', dest='appID',
                        help='application Identifier',
                        default='256')
    parser.add_argument('-items', dest='itemList',
                        help='comma-separated list of RICs')
    parser.add_argument('-vfids', dest='viewFIDs',
                        help='comma-separated list of Field IDs for View')
    parser.add_argument('-vnames', dest='viewNames',
                        help='comma-separated list of Field Names for View')
    parser.add_argument('-md', dest='domain',
                        help='domain model - server defaults to MarketPrice.\
                            Numeric or name - 6 / MarketPrice, 7 / MarketByOrder, 8 / MarketByPrice')
    parser.add_argument('-f', dest='ricFile',
                        help='simple file of RICs - one per line')
    parser.add_argument('-ef', dest='ricFileExt',
                        help='multi domain file of numeric domain|RIC - e.g. 7|VOD.L')
    parser.add_argument('-t', dest='snapshot',
                        help='Snapshot request',
                        default=False,
                        action='store_true')
    parser.add_argument('-X', dest='dump',
                        help='Output Received JSON Data messages to console',
                        default=False,
                        action='store_true')
    parser.add_argument('-l', dest='logFilename',
                        help='Redirect console to filename',
                        default=None)
    parser.add_argument('-e', dest='autoExit',
                        help='Auto Exit after all items retrieved',
                        default=False,
                        action='store_true')
    parser.add_argument('-et', dest='exitTimeMins',
                        help='Exit after time in minutes (0=indefinite)',
                        type=int,
                        default=0)
    parser.add_argument('-st', dest='statsTimeSecs',
                        help='Show Statistics interval in seconds',
                        type=int,
                        default=5)
    parser.add_argument('-ss', dest='showSentMsgs',
                        help='Output the JSON messages sent to server',
                        default=False,
                        action='store_true')
    parser.add_argument('-sp', dest='showPingPong',
                        help='Output Ping and Pong heartbeat messages',
                        default=False,
                        action='store_true')
    parser.add_argument('-sos', dest='showStatusMsgs',
                        help='Output received Status messages',
                        default=False,
                        action='store_true')
    
    return (parser.parse_args(args))

# Get auth tokens from auth server
def get_sts_token(current_refresh_token):
    """ 
        Retrieves an authentication token. 
        :param current_refresh_token: Refresh token retrieved from a previous authentication, used to retrieve a
        subsequent access token. If not provided (i.e. on the initial authentication), the password is used.
    """
    
    url = 'https://{}:{}/{}'.format(opts.authHostname, opts.authPort, auth_path)

    if not current_refresh_token:  # First time through, send password
        data = {'username': opts.user, 'password': opts.password, 'grant_type': 'password', 'takeExclusiveSignOnControl': True,
                'scope': scope}
        print("Sending authentication request with password to ", url, "...")
    else:  # Use the given refresh token
        data = {'username': opts.user, 'refresh_token': current_refresh_token, 'grant_type': 'refresh_token',
                'takeExclusiveSignOnControl': True}
        print("Sending authentication request with refresh token to ", url, "...")

    try:
        r = requests.post(url,
                          headers={'Accept': 'application/json'},
                          data=data,
                          auth=(opts.user, client_secret),
                          verify=True)

    except requests.exceptions.RequestException as e:
        print('EDP-GW authentication exception failure:', e)
        return None, None, None

    if r.status_code != 200:
        print('EDP-GW authentication result failure:', r.status_code, r.reason)
        print('Text:', r.text)
        if r.status_code == 401 and current_refresh_token:
            # Refresh token may have expired. Try using our password.
            return get_sts_token(None)
        return None, None, None

    auth_json = r.json()
    print("EDP-GW Authentication succeeded. RECEIVED:")
    print(json.dumps(auth_json, sort_keys=True, indent=2, separators=(',', ':')))

    return auth_json['access_token'], auth_json['refresh_token'], auth_json['expires_in']


if __name__ == '__main__':
    opts = parse_args(sys.argv[1:])
    # print("Invoked with:", opts)
    if not validate_options():
        print('Exit due to invalid arguments')
        sys.exit(2)

    #  Redirect console to file if logFilename specified
    orig_stdout = sys.stdout
    if (opts.logFilename!=None):
        try:
            print('Redirecting console to file "{}"'.format(opts.logFilename))
            sys.stdout = open(opts.logFilename, "w")
        except IOError:
            print('Could not redirect console to file "{}"'.format(opts.logFilename))
            sys.stdout = orig_stdout
            sys.exit(2)

    if edp_mode:    # Are we going to connect to EDP
        sts_token, refresh_token, expire_time = get_sts_token(None)
        if not sts_token:
            print("Could not get authorisaton token")
            sys.exit(1)

    # Set our EDP or ADS Login request credentials
    market_data.set_Login(opts.user,
                        opts.appID,
                        opts.position,
                        sts_token,
                        edp_mode)

    market_data.dumpRcvd = opts.dump
    market_data.dumpPP = opts.showPingPong
    market_data.dumpSent = opts.showSentMsgs
    market_data.dumpStatus = opts.showStatusMsgs
    market_data.autoExit = opts.autoExit

    # User wants to exit once all item responsed from server 
    # So switch to Snapshot mode.
    if (opts.autoExit):
        opts.snapshot=True
        print("AutoExit selected so enabling Snapshot mode too")

    market_data.set_Request_Attr(opts.service,simpleRics,opts.domain,opts.snapshot,extRics)

    if (opts.viewNames!=None):
        vList = opts.viewNames.split(',')
        market_data.set_viewList(vList)
    elif (opts.viewFIDs!=None):
        vList = list(map(int, opts.viewFIDs.split(',')))
        market_data.set_viewList(vList)

    # Start websocket handshake
    # Use 'wss' for edp connection or 'ws' for ADS connection
    protocol = "wss" if edp_mode else "ws"
    ws_address = protocol +"://{}:{}/WebSocket".format(opts.host, opts.port)
    print("Connecting to WebSocket " + ws_address + " ...")
    ws_app = websocket.WebSocketApp(ws_address, header=['User-Agent: Python'],
                                        on_message=market_data.on_message,
                                        on_error=market_data.on_error,
                                        on_close=market_data.on_close,
                                        subprotocols=['tr_json2'])
    ws_app.on_open = market_data.on_open
    # Event loop
    wst = threading.Thread(target=ws_app.run_forever, kwargs={'sslopt': {'check_hostname': False}})
    wst.start()

    # Now lets run a loop to allow time to send and receive async responses from server
    try:
        # Determine how often to output basic stats
        stat_time = time.time() + opts.statsTimeSecs
        # When do we next need to reissue the auth token
        reissue_token_time = time.time() + (int(expire_time) - 30)
        
        # When should we stop looping and exit
        end_time = None
        if (opts.exitTimeMins>0):   # Are we looping for limited time
            end_time = time.time() + 60*opts.exitTimeMins
            print("Run for", opts.exitTimeMins, "minute(s)")
        else:
            print("Run indefinitely - CTRL+C to break")

        # Loop forever or until specified end time or shutdown signalled
        while (((opts.exitTimeMins==0) or (time.time() < end_time)) 
                    and (not market_data.shutdown_app)):
            
            time.sleep(1)

            # If we are connected to EDP, check if its time to re-authorise
            if ((edp_mode) and time.time()>=reissue_token_time):
                sts_token, refresh_token, expire_time = get_sts_token(refresh_token)
                if not sts_token:
                    print("Could not get authorisaton token")
                    break
                if market_data.logged_in:
                    market_data.reissue_token(ws_app,sts_token)
                # Reset the token reissue time
                reissue_token_time = time.time() + (int(expire_time) - 30)

            # Is is time to print some basic stats?
            if (time.time() >= stat_time):
                market_data.print_stats()
                stat_time = time.time() + opts.statsTimeSecs
            
            # Check to see if we have not received a PING from server in a while
            if market_data.ping_timedout():
                break   # Exit loop and app

    except KeyboardInterrupt:
        pass
    finally:
        ws_app.close()
        market_data.print_stats()

    sys.stdout = orig_stdout
#
#
#
