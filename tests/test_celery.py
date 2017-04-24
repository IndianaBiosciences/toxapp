import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

# currently using file system as messaging backend ... as note indicates in tasks change this later to DB
# as root run
# sudo mkdir -p /tmp/celery/results
# sudo chmod 777 /tmp/celery/results

# change to toxapp base directory
# run the worker as:
# celery -A toxapp worker --loglevel=info

from tp.tasks import add
import time

res = add.delay(5,2)
time.sleep(5)
print(res.ready())
print(res.get(timeout=1))
