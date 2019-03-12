# Python Websocket API Test Client  

* [Overview](#overview)
* [Setup](#setup)
* [Optional Arguments](#arguments)
* [Example Runtime Scenarios](#runtime)

## <a id="overview"></a>Overview 

Python example that uses the Refinitiv Websocket interface to facilitate the consumption of realtime data.
This example is meant to be a simplistic version of the 'rmdstestclient' tool and illustrates a variety of scenarios such as:  
* EDP or ADS connection
* Batch / View Request
* Streaming / Snapshot
* Reuters Domain Models

## Disclaimer  
The source code presented in this project has been written by Refinitiv solely for the purpose of illustrating the concepts of using the Websocket interface.  None of the code has been tested for a usage in production environments.

## <a id="setup"></a>Setup 
### Windows/Linux/macOS
1. __Install Python__
    - Go to: <https://www.python.org/downloads/>
    - Select the __Download tile__ for the Python 3 version
    - Run the downloaded `python-<version>` file and follow installation instructions
2. __Install libraries__
    - Run the following (which installs 'requests' and 'websocket-client'):
      - `pip install -r requirements.txt`
3. __Login Credentials__
    - You will need the following:
      - To Login to an ADS server 
        - the hostname/ip + port number of the ADS  
        - DACS username  
      - For EDP connection  
        - EDP server data url
        - EDP Authentication server url
        - Your EDP username and password
  

## <a id="arguments"></a>Optional arguments:  


| Argument | Description                              |
|-----------|------------------------------------------|
| -h        | Show this help message and exit          |
| -S        | Service name to request from (default: None - however, server typically has default) |
| -H        | Hostname of ADS server or EDP endpoint (default: ads1) |
| -ah       | Authorization server (default: api.edp.thomsonreuters.com) |
| -p        | Port of the ADS server or EDP (default: 15000) |
| -ap       | Port of the authorisation server (default: 443) |
| -u        | Login user name (default: your local os username) |
| -pw       | Specify EDP user password to connect to EDP (default: None) |
| -pos      | Application position (default: your local IP address) |
| -aid      | Application Identifier (default: 256)    |
| -items    | comma-separated list of RICs (default: None) |
| -vfids    | comma-separated list of Field IDs for View (default: None) |
| -vnames   | comma-separated list of Field Names for View (default: None) |
| -f        | Filename of simple RICs - one per line (default: None) |
| -ef       | Filename of multi domain RICs - e.g. 6\|VOD.L (default: None) |
| -md       | Domain Model (default:None - however, server defaults to MarketPrice)<br>Accepts numeric or name e.g. 6 or MarketPrice, 7 or MarketByOrder, 8 or MarketByPrice  |
| -t        | Snapshot request (default: False)        |
| -X        | Output Received JSON Data messages to console (default: False) |
| -l        | Redirect console to filename (default: None) |
| -e        | Auto Exit after all items retrieved (default: False) |
| -et       | Exit after time in minutes (0=indefinite) (default: 0) |
| -st       | Show Statistics interval in seconds (default: 10) |
| -ss       | Output the JSON messages sent to server (default: False) |
| -sp       | Output Ping and Pong heartbeat messages (default: False) |
| -sos      | Output received Status messages (default: False) |


 

    
  
## <a id="runtime"></a>Example runtime scenarios  
Below are a few example scenarios with sample arguments

**Connect to EDP, request MarketPrice items from default service and display summary stats**  
    -H emea-1.pricing.streaming.edp.thomsonreuters.com -p 443 -items VOD.L,BT.L -u \<EDP Username\> -pw \<EDP Password\>   
    
**Connect to ADS, request MarketPrice items from ELEKTRON_DD service and display summary stats**  
    -S ELEKTRON_DD -H ads1 -items VOD.L,MSFT.O,TRI.N -u umer.nalla
    
**Connect to ADS, request MarketPrice items from default service and display summary stats**  
    -H ads1 -items VOD.L,MSFT.O,TRI.N -u umer.nalla

**As above and display received data**  
    -H ads1 -items VOD.L,MSFT.O,TRI.N -u umer.nalla -X

**As above with output redirected to file log.out**  
    -H ads1 -items VOD.L,MSFT.O,TRI.N -u umer.nalla -X -l log.out

**As above except request MarketByPrice data**  
    -H ads1 -md MarketByPrice -items VOD.L,BT.L,BP.L -u umer.nalla -X -l log.out

**As above except using numeric Domain value**  
    -H ads1 -md 8 -items VOD.L,BT.L,BP.L -u umer.nalla -X -l log.out

**MarketPrice request for RICs read from file srics.txt (one RIC per line)**  
    -H ads1 -f srics.txt -u umer.nalla -X -l log.out

**MarketByOrder request for RICs read from file srics.txt (one RIC per line)**  
    -H ads1 -f srics.txt -md MarketByOrder -u umer.nalla -X -l log.out

**As above except mixed Domain RICs read from file extrics.txt (numeric domain|RIC per line)**  
    -H ads1 -ef extrics.txt -u umer.nalla -X -l log.out


    