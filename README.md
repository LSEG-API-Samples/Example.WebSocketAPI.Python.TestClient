<a href="https://developers.refinitiv.com" target="_blank">Refinitiv Developer Portal</a>   
<a href="https://community.developers.refinitiv.com/questions/index.html" target="_blank">Refinitiv Developer Community Forums</a>

# Python Websocket API Test Client  

* [Overview](#overview)
* [Setup](#setup)
* [Optional Arguments](#arguments)
* [Example Runtime Scenarios](#runtime)

## <a id="overview"></a>Overview 

Python example that uses the Refinitiv Websocket interface to facilitate the consumption of realtime data.
This example is meant to be a simplistic version of the 'rmdstestclient' tool and illustrates a variety of scenarios such as:  
* RDP or ADS connection
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
      - For RDP connection  
        - RDP server data url
        - RDP Authentication server url
        - Your RDP username and password
  

## <a id="arguments"></a>Optional arguments:  


| Argument | Description                              |
|-----------|------------------------------------------|
| -h        | Show this help message and exit          |
| -S        | Service name to request from (default: None - however, server typically has default) |
| -H        | Hostname of ADS server or RDP endpoint (default: ads1) |
| -ah       | Authorization server (default: api.refinitiv.com) |
| -p        | Port of the ADS server or RDP (default: 15000) |
| -ap       | Port of the authorisation server (default: 443) |
| -u        | Login user name (default: your local os username) |
| -pw       | Specify RDP user password to connect to RDP (default: None) |
| -c        | RDP ClientID aka AppKey - generated using AppKey Generator (default: None) |
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

**Connect to RDP, request MarketPrice items from default service and display summary stats**  
    -H emea-1.pricing.streaming.edp.thomsonreuters.com -p 443 -items VOD.L,BT.L -u \<RDP Username\> -pw \<RDP Password\> -c \<ClientID/AppKey\>  
    
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

**MarketPrice View (FIDs TRDPRC_1,BID,ASK) request for RICs read from file srics.txt**  
    -H ads1 -f srics.txt -vfids 6,22,25 -u umer.nalla -X -l log.out 

**MarketByOrder request for RICs read from file srics.txt (one RIC per line)**  
    -H ads1 -f srics.txt -md MarketByOrder -u umer.nalla -X -l log.out

**As above except mixed Domain RICs read from file extrics.txt (numeric domain|RIC per line)**  
    -H ads1 -ef extrics.txt -u umer.nalla -X -l log.out


### <a id="contributing"></a>Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

### <a id="authors"></a>Authors

* **Umer Nalla** - Release 1.1.  *Partial Rebrand version*

### <a id="license"></a>License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
    
