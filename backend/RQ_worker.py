from redis import Redis
from rq import Queue
from rq.worker import SimpleWorker

redis_conn = Redis(host="localhost", port=6379, db=0, protocol=2)
queue = Queue("reviews", connection=redis_conn)

if __name__ == "__main__":
    worker = SimpleWorker([queue], connection=redis_conn)
    worker.work()