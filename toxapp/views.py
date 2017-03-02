from django.http import HttpResponse
from django.template import loader

def index(request):
    """
    View function for home page of site.
    """
    template = loader.get_template('index.html')
    context = {

    }
    return HttpResponse(template.render(context, request))

def profile(request):
    """
    Expose the user profile and tools to the user
    """
    context = {

    }
    template = loader.get_template('registration/profile.html')
    return HttpResponse(template.render(context, request))