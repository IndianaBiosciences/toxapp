from django.contrib import admin

# Expose the Experiment Model on the Admin Site
from tp.models import Experiment
#todo: register more models?
admin.site.register(Experiment)
