"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, re_path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.documentation, name='documentation'),    # http://127.0.0.1:8000/  or https://table-catcher.herokuapp.com/
    path('scan_tables/', views.scan_tables, name='scan_tables'),   # POST request
    # re_path(r'^get/$', views.get_data, name='get_data'),   # http://127.0.0.1:8000/get/?topic=https://coinmarketcap.com/
]
