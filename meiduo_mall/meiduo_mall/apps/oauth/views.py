from django.shortcuts import render

from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http


# Create your views here.
class QQAuthURLView(View):
    # 提供qq登录扫码页面
    def get(self, request):
        # 接收参数 next
        # 创建工具对象
        # 生成qq登录扫码链接地址
        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET, redirect_uri='',
                        state='next')
        # 生成qq登录扫码链接地址
        login_url = oauth.get_qq_url()
        return http.JsonResponse({'code': 'ok', 'errmsg': 'ok', 'login_url': login_url})
