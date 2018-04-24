# smart-man-in-the-middle
A TCP proxy with SSL support on left side and smart messages handling

# Usage
Usage: smart-man-in-the-middle.py [-h] [-d] -l 0.0.0.0:8844 -r
                                  remote-destination.com:9955
                                  [-lk /path/to/left-side.key]
                                  [-lc /path/to/left-side.crt]
                                  -ew 0x0011223344556677889900112233445566778899
                                  [-ef fees]

Optional arguments:
  * -h, --help            show this help message and exit
  * -d, --debug           Set default logger level to DEBUG instead of INFO  
                          (default: False)
  * -l 0.0.0.0:8844, --left 0.0.0.0:8844
                          Bind address for left proxy side (default: None)
  * -r remote-destination.com:9955, --right remote-destination.com:9955
                          Destination for right proxy side (default: None)
  * -lk /path/to/left-side.key, --left-key /path/to/left-side.key  
                          Path to SSL private key file for left proxy side  
                          (default: None)
  * -lc /path/to/left-side.crt, --left-cert /path/to/left-side.crt  
                          Path to SSL public certificate file for left proxy  
                          side (default: None)
  * -ew 0x0011223344556677889900112233445566778899,, --eth-wallet 0x0011223344556677889900112233445566778899  
                          Your Ethereum wallet address  default: None)
                          (default: None)
  * -ef fees, --eth-fees-worker fees  
                          An alternate worker name when doing subtitution (default: None)

# TODO

  * Proper handling of SIGTERM, for some reason it's not behaving as the asyncio doc says it will
  * I know it's half python3.4 (coroutine/yield), half python3.5 (unpacking in loggers), move to async/await syntax
