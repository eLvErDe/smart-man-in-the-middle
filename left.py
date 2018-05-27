import asyncio
import json
from right import Right

class Left(asyncio.Protocol):

    SEP = b'\n'
    TIMEOUT = 600

    def __init__(self, logger, loop, dest, eth_my_wallet, eth_fees_worker, server):
        self.logger = logger
        self.loop = loop
        self.dest = dest
        self.server = server
        self.buffer = bytes()
        self.w_q = asyncio.Queue()
        self.transport = None
        self.peername = (None, None)
        self.eth_my_wallet = eth_my_wallet
        self.eth_fees_worker = eth_fees_worker
        self.eth_is_fee = False

    def connection_made(self, transport):

        self.transport = transport
        self.peername = self.transport.get_extra_info('peername')
        self.logger.info('[%s:%s] Left-side connection made', *self.peername)
        self.h_timeout = self.loop.call_later(self.TIMEOUT, self.timeout)

        # Start remote endpoint connection with callback to retrieve
        # Exception and closed if it failed
        self.right = Right(self.logger, self.loop, self)
        coro = self.loop.create_connection(lambda: self.right, *self.dest)
        task = self.loop.create_task(coro)

        def connection_check_for_failure(fut):
            exc = fut.exception()
            if exc is not None:
                self.logger.error("[%s:%s] Connection to %s:%s failed: %s", *self.peername, *self.dest, exc)
                self.transport.close()
            else:
                self.logger.info('[%s:%s] Connection proxied to %s:%s successfully', *self.peername, *self.dest)
                self.q_consumer = asyncio.ensure_future(self.consume())

        task.add_done_callback(connection_check_for_failure)

    @asyncio.coroutine
    def consume(self):

        self.logger.debug('[%s:%s] Left-side transport write queue consumer started', *self.peername)
        while not self.transport.is_closing():
            try:
                message = yield from self.w_q.get()
                self.logger.debug('[%s:%s] <- [%s:%s] %r', *self.peername, *self.right.peername, message)
                self.transport.write(message + self.SEP)
            except asyncio.CancelledError:
                self.logger.warning('[%s:%s] Left-side consume coroutine has been stopped', *self.peername)
                return
            except Exception as e:
                self.logger.error('[%s:%s] Left-side had an exception consume coroutine: %s: %s', *self.peername, e.__class__.__name__, e)

    def data_received(self, data):

        self.h_timeout.cancel()
        self.h_timeout = self.loop.call_later(self.TIMEOUT, self.timeout)

        self.buffer += data

        messages = self.buffer.split(self.SEP)

        if data.endswith(self.SEP):
            self.buffer = bytes()
        else:
            incomplete = messages.pop()
            self.logger.warning('[%s:%s] Left-side received incomplete message: %r will be sent later', *self.peername, incomplete)
            self.buffer = incomplete

        for message in messages:

            if not message:
                continue

            try:

                d_message = json.loads(str(message, 'utf-8'))

                if d_message['method'] == 'eth_submitLogin':

                    self.logger.info('[%s:%s] Found eth_submitLogin message: %s', *self.peername, message)

                    worker = d_message['worker']
                    username, password = d_message['params']
                    wallet = username[:42]
                    self.logger.info('[%s:%s] Worker name: %s', *self.peername, worker)
                    self.logger.info('[%s:%s] Username/password: %s/%s', *self.peername, username, password)
                    self.logger.info('[%s:%s] Wallet address: %s', *self.peername, wallet)

                    if wallet.lower() != self.eth_my_wallet:
                        self.logger.warning('[%s:%s] Replacing wallet %s by %s', *self.peername, wallet, self.eth_my_wallet)
                        self.eth_is_fee = True
                        d_message['params'][0] = d_message['params'][0].replace(wallet, self.eth_my_wallet)

                # This connection is being used for fees
                if self.eth_is_fee:
                    if 'worker' in d_message and self.eth_fees_worker is not None:
                        worker = d_message['worker']
                        self.logger.warning('[%s:%s] Replacing worker name %s by %s', *self.peername, worker, self.eth_fees_worker)
                        d_message['worker'] = self.eth_fees_worker

                message = bytes(json.dumps(d_message), 'utf-8')

            except Exception as e:
                self.logger.exception('[%s:%s] Message %s parsing failed with %s: %s', *self.peername, message, e.__class__.__name__, e)

            if message:
                # Right side not connected yet but left side is talking already
                if self.right.transport is None:
                    self.logger.warning('[%s:%s] Left-side received message but remote endpoint is not connected yet: %r will be sent later', *self.peername, message + self.SEP)
                self.right.w_q.put_nowait(message)

    def eof_received(self):
        pass

    def connection_lost(self, exc):
        self.logger.error('[%s:%s] Left-side connection lost', *self.peername)

        if hasattr(self, 'transport'):
            self.h_timeout.cancel()

            # Queue consumer won't be create if it never connects right side
            if hasattr(self, 'q_consumer'):
                self.q_consumer.cancel()  # pylint: disable=no-member

            # Properly close right side
            if self.right.transport is not None:
                self.right.transport.close()

    def timeout(self):

        self.logger.error('[%s:%s] Left-side connection timed out after %ds of inactivity', *self.peername, self.TIMEOUT)
        self.transport.close()
