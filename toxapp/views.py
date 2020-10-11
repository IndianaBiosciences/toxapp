# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from toxapp.forms import SignUpForm
from django.core.mail import send_mail
from django.conf import settings

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

def about(request):
    """
    Expose the user profile and tools to the user
    """
    context = {

    }
    template = loader.get_template('about.html')
    return HttpResponse(template.render(context, request))

def training(request):
    """
    Expose the user profile and tools to the user
    """
    context = {

    }
    template = loader.get_template('training.html')
    return HttpResponse(template.render(context, request))

def references(request):
    """
    Expose the user profile and tools to the user
    """
    context = {

    }
    template = loader.get_template('references.html')
    return HttpResponse(template.render(context, request))

def videos(request):
    """
    Expose the user profile and tools to the user
    """
    context = {

    }
    template = loader.get_template('videos.html')
    return HttpResponse(template.render(context, request))

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            user.is_active = False
            user.save()
            if(hasattr(settings, 'ACCOUNTS_EMAIL')):
                subject = str(user.email) + ' Signed Up'
                message = ' Username: ' + str(username)+ ' Email: '+ str(user.email)
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [settings.ACCOUNTS_EMAIL, ]
                send_mail(subject, message, email_from, recipient_list)
            #login(request, user)
            return redirect(index)
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def data(request):
    """
    Expose data options to the user
    """
    context = {

    }
    template = loader.get_template('data.html')
    return HttpResponse(template.render(context, request))

def filters(request):
    """
    Expose results filtering options to the user
    """
    context = {

    }
    template = loader.get_template('filters.html')
    return HttpResponse(template.render(context, request))
