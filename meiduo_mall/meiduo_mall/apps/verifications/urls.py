from django.conf.urls import url
from . import views
urlpatterns = [
    # 图形验证码
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),
    url(r'^sms_codes/(?P<mobile>[\w-]+)/$', views.SMSCodeView.as_view()),
]

