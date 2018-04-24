#!/usr/bin/python3

import sys
import os
import logging
import argparse
import asyncio
import ssl
from left import Left

NAME = 'smart-man-in-the-middle'

def set_proc_name(name, logger):
     try:
         from setproctitle import setproctitle
         setproctitle(name)
     except ImportError:
         logger.error('Setproctitle module not avaible, process name not renamed')

def get_args():

    def host_port(s):
        try:
            host, port = s.split(':')
            port = int(port)
            return host, port
        except:
            raise argparse.ArgumentTypeError('Hostname must be address:port')

    parser = argparse.ArgumentParser(description='A TCP proxy with SSL support on left side and smart messages handling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d',  '--debug',      action='store_true',             help='Set default logger level to DEBUG instead of INFO')
    parser.add_argument('-l',  '--left',       type=host_port,  required=True,  help='Bind address for left proxy side', metavar='0.0.0.0:8844')
    parser.add_argument('-r',  '--right',      type=host_port,  required=True,  help='Destination for right proxy side', metavar='remote-destination.com:9955')
    parser.add_argument('-lk', '--left-key',   type=str,        required=False, help='Path to SSL private key file for left proxy side', metavar='/path/to/left-side.key')
    parser.add_argument('-lc', '--left-cert',  type=str,        required=False, help='Path to SSL public certificate file for left proxy side', metavar='/path/to/left-side.crt')
    parser.add_argument('-ew', '--eth-wallet', type=str,        required=True,  help='Your Ethereum wallet address', metavar='0x0011223344556677889900112233445566778899')
    parser.add_argument('-ef', '--eth-fees-worker', type=str,   required=False, help='An alternate worker name when doing subtitution', metavar='fees')

    parsed = parser.parse_args()

    if (parsed.left_key and not parsed.left_cert) or (parsed.left_cert and not parsed.left_key):
        raise argparse.ArgumentTypeError('Specified both key and cert or none of them')

    if not parsed.eth_wallet.startswith('0x'):
        raise argparse.ArgumentTypeError('Ethereum wallet address should start with 0x')
    if len(parsed.eth_wallet) != 42:
        raise argparse.ArgumentTypeError('Ethereum wallet address should be 42 characters')
    parsed.eth_wallet = parsed.eth_wallet.lower()

    return parser.parse_args()


if __name__ == '__main__':

    # Proper terminal size when displaying --help
    try:
        from os import environ
        from shutil import get_terminal_size
        environ['COLUMNS'] = str(get_terminal_size().columns)
    except:
        pass

    # Command line arguments
    config = get_args()

    # Logger
    log_level = logging.DEBUG if config.debug else logging.INFO 
    logging.basicConfig(stream=sys.stdout, level=log_level, format='%(asctime)s %(levelname)-8s %(message)s',)
    logger = logging.getLogger(__name__)
    logger.info('Will substitute wallets with %s on eth_submitLogin messages', config.eth_wallet)

    # Process name
    set_proc_name(NAME + ' ' + ' '.join(sys.argv[1:]), logger)

    # Prepare asyncio left server (and right parameter)
    bind = config.left
    dest = config.right
    logger.info('Adding server bind on %s:%s proxying to %s:%s', *bind, *dest)

    # Prepare SSL context for left server
    if config.left_key:
        sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        sslctx.load_cert_chain(certfile=config.left_cert, keyfile=config.left_key)
    else:
        sslctx = None

    # Run left server (will connect right side when connection made on left side)
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: Left(logger, loop, dest, config.eth_wallet, config.eth_fees_worker, server), *bind, ssl=sslctx)
    server = loop.run_until_complete(coro)

    try:
        logger.info('Starting asyncio loop')
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
