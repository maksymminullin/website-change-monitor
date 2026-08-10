import asyncio
import signal

from app.worker.scheduler import setup_scheduler


async def main() -> None:
    scheduler = setup_scheduler()
    scheduler.start()

    stop_event = asyncio.Event()

    def handle_sigterm():
        scheduler.shutdown()
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigterm)

    await stop_event.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
