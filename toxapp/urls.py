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

"""toxapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

admin.site.site_header = "IBRI Toxicogenomics Platform | Admin"

app_name = "toxapp"

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^profile/$', views.profile, name='profile'),

    url(r'^about/$', views.about, name='about'),

    url(r'^training/$', views.training, name='training'),

    url(r'^references/$', views.references, name='references'),

    url(r'^videos/$', views.videos, name='videos'),

    url(r'^admin/', admin.site.urls),

    url(r'^', include('django.contrib.auth.urls')),

    url(r'', include('tp.urls', namespace='tp')),

    url(r'^signup/$', views.signup, name='signup'),

    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    url(r'^data/$', views.data, name='data'),

    url(r'^filters/$', views.filters, name='filters'),
]
