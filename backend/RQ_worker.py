from redis import Redis
from rq import Queue
from rq.worker import SimpleWorker
from config import settings

redis_conn = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    protocol=2
)
queue = Queue("reviews", connection=redis_conn)

if __name__ == "__main__":
    worker = SimpleWorker([queue], connection=redis_conn)
    worker.work()