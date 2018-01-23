import asyncio


class Right(asyncio.Protocol):

    SEP = b'\n'

    def __init__(self, logger, loop, left):
        self.logger = logger
        self.loop = loop
        self.left = left
        self.buffer = bytes()
        self.transport = None
        self.w_q = asyncio.Queue()
        self.peername = (None, None)

    def connection_made(self, transport):

        self.transport = transport
        self.peername = self.transport.get_extra_info('peername')
        self.logger.info('[%s:%s] Right-side connection to %s:%s establised', *self.left.peername, *self.peername)

        self.q_consumer = asyncio.ensure_future(self.consume())

    @asyncio.coroutine
    def consume(self):

        self.logger.debug('[%s:%s] Right-side transport write queue consumer started', *self.left.peername)
        while not self.transport.is_closing():
            try:
                message = yield from self.w_q.get()
                self.logger.debug('[%s:%s] -> [%s:%s] %r', *self.left.peername, *self.peername, message)
                self.transport.write(message + self.SEP)
            except asyncio.CancelledError:
                self.logger.warning('[%s:%s] Right-side consume coroutine has been stopped', *self.left.peername)
                return
            except Exception as e:
                self.logger.error('[%s:%s] Right-side had an exception consume coroutine: %s: %s', *self.left.peername, e.__class__.__name__, e)

    def data_received(self, data):
        self.buffer += data

        messages = self.buffer.split(self.SEP)

        if data.endswith(self.SEP):
            self.buffer = bytes()
        else:
            incomplete = messages.pop()
            self.logger.warning('[%s:%s] Right-side received incomplete message: %r will be sent later', *self.left.peername, incomplete)
            self.buffer = incomplete

        for message in messages:
            if message:
                self.left.w_q.put_nowait(message)

    def eof_received(self):
        pass

    def connection_lost(self, exc):
        self.logger.error('[%s:%s] Right.side connection lost', *self.left.peername)

        if hasattr(self, 'q_consumer'):
            self.q_consumer.cancel()  # pylint: disable=no-member

        # Close the left proxy side as well
        self.left.transport.close()
