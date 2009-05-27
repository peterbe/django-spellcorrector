from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    url(r'^/?$', views.documents, name="documents"),
    url(r'^a-la-google/$', views.documents_a_la_google, 
        name="documents_a_la_google"),
)                       