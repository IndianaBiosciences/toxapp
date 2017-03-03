from django.contrib import admin

# Expose the Experiment Model on the Admin Site
from tp.models import Experiment

admin.site.register(Experiment)
