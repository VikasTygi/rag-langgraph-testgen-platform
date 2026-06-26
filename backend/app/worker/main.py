import asyncio
import logging

from app.worker.sqs_consumer import consume_forever


logging.basicConfig(level=logging.INFO)


def main():
    asyncio.run(consume_forever())


if __name__ == "__main__":
    main()