import os
import time
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toxapp.settings")
application = get_wsgi_application()

from tp.tasks import add

res = add.delay(5,2)
time.sleep(5)
print(res.ready())
print(res.get(timeout=1))
