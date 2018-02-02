from celery import Celery
import time

# run the worker as celery -A test_celery_standalone worker --loglevel=info
# as root run
# sudo mkdir -p /tmp/celery/results
# sudo chmod 777 /tmp/celery/results
app = Celery('test_celery_standalone', backend='file:///tmp/celery/results', broker='amqp://guest:guest@localhost:5672//')

@app.task
def add(x, y):
    return x + y

if False:

    res = add.delay(5,2)
    time.sleep(5)
    print(res.ready())
    print(res.get(timeout=1))
