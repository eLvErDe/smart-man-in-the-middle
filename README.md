# smart-man-in-the-middle
A TCP proxy with SSL support on left side and smart messages handling

# Usage
Usage: smart-man-in-the-middle.py [-h] [-d] -l 0.0.0.0:8844 -r
                                  remote-destination.com:9955
                                  [-lk /path/to/left-side.key]
                                  [-lc /path/to/left-side.crt]
                                  [-ls original_str replacement_str]

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
  * -ls original_str replacement_str, --left-sub original_str replacement_str  
                          Substitute str1 with str2 in message coming from left  
                          side (default: [])
