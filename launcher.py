import asyncio
import asyncpg
import logging
import contextlib
from logging.handlers import RotatingFileHandler

from bot import RU_COMSCI_bot

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record):
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(filename='RUCS_BOT.log', encoding='utf-8', mode='w', maxBytes=max_bytes,
                                      backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


def main():
    with setup_logging():
        asyncio.run(run_bot())


async def run_bot():
    log = logging.getLogger()
    # localhost = {
    #     "user": "postgres",
    #     "password": "password",
    #     "database": "postgres",
    #     "host": "localhost",
    #     "port": "5432",
    # }
    # kwargs = {
    #     'command_timeout': 60,
    #     'max_size': 20,
    #     'min_size': 20,
    # }
    # try:
    #     pool = await asyncpg.create_pool(**localhost, **kwargs)
    # except Exception as e:
    #     log.exception('could not set up PostgreSQL. Exiting.')
    bot = RU_COMSCI_bot()
    # bot.pool = pool
    await bot.start()


if __name__ == '__main__':
    with contextlib.suppress(KeyboardInterrupt):
        main()
