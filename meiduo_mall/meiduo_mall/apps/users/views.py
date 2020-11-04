from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
from users.models import User
from django.db import DatabaseError
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection


class LoginView(View):
    def get(self, request):
        # 提供用户登录页面
        return render(request, 'login.html')

    def post(self, request):
        # 实现用户登录逻辑
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必要参数')

        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名和手机号')

        # 判断密码是否是8-20个字符
        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden('登录密码最少8位，最长20位')

        # 认证用户，使用账号查询用户是否存在，如果用户存在再去校验密码是否正确
        # User.objects.get(username=username)
        # User.check_password(password)
        user = authenticate(username=username, password=password)
        if user is None:
            # return '错误提示信息 json html 403'  403只用于校验参数，前端校验过的 后端校验仍旧错误，登录用表单提交所以不用json
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})

        # 状态保持
        login(request, user)
        # 使用remember确定状态保持周期，实现记住登录，记住用户
        if remember != 'on':
            # 没有记住登录：状态保持在浏览器会话结束后就销毁
            request.session.set_expiry(0)
        else:
            # 记住登录：状态保持周期为2周,默认是2周 传None，3600s 单位是s
            request.session.set_expiry(None)

        # 响应结果
        return redirect(reverse('contents:index'))


# Create your views here.
class UsernameCountView(View):
    # 判断用户名是否重复注册
    def get(self, request, username):
        # 接收和校验参数

        # 实现主体业务逻辑：使用username查询对应的记录的条数
        # filter返回的是满足条件的结果集
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'count': count,
        })
        # 响应结果


class MobileCountView(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'count': count,
        })


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        # 提供用户注册页面
        return render(request, 'register.html')

    def post(self, request):
        # 实现用户注册逻辑
        # 接收参数
        # value = request.POST.get('key')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')
        # return render(request, 'register_data')
        # 校验参数：前后端的校验分开，避免恶意用户越过前端逻辑发送请求，前后端的校验逻辑要相同
        # 判断参数是否齐全,判断其他数据是否正确
        # all() 会去校验列表中的元素是否为空，只要有一个为空，返回false
        if not all([username, password, password2, mobile, allow]):
            # return '如果缺少必传参数，响应错误提示信息，403'
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('注册密码最少8位，最长20位')
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')

        # 判断短信验证码是否正确
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile).decode()
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
        if sms_code_client != sms_code_server:
            return render(request, 'register.html', {'sms_code_errmsg': '输入的短信验证码错误'})

        # 判断是否
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 保存注册数据,是注册的核心
        # return render(request, 'register.html', {'register_error': '注册失败'})
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_error': '注册失败'})
        # 实现状态保持
        login(request, user)

        # 响应结果:重定向到首页
        # return redirect('/') 如果改掉地址，会导致访问失败
        # return redirect(reverse('命名空间'))
        # return redirect(reverse('总路由的namespace:子路由的name'))
        # reverse('contents:index') == '/'
        return redirect(reverse('contents:index'))
