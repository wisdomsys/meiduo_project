import json
import logging

from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
from users.models import User
from django.db import DatabaseError
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url, check_verify_email_token

# 创建日志输出器
logger = logging.getLogger('django')


class VerifyEmailView(View):
    # 验证邮箱
    def get(self, request):
        # 接收参数
        token = request.GET.get('token')
        # 校验参数
        if not token:
            return http.HttpResponseForbidden('缺少token')
        # 从token中提取用户的信息 user_id ==> user
        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseBadRequest('无效的token')
        # 将用户的email_active字段设置为true
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')
        # 响应结果  重定向到用户中心
        return redirect('users:info')


class EmailView(LoginRequiredJSONMixin, View):
    # 添加邮箱
    def put(self, request):
        # 将用户传入的邮箱保存到数据库的email字段中
        # 接收参数
        json_str = request.body.decode()  # body类型是bytes
        json_dict = json.loads(json_str)  # 将json格式数据转换为字典（可以这么理解，json.loads()函数是将字符串转化为字典）
        email = json_dict.get('email')
        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': '1', 'errmsg': '添加邮箱失败'})
        # 发送邮箱验证邮件
        verify_url = generate_verify_email_url(request.user)
        # send_verify_email(email, verify_url) 错误的写法
        send_verify_email.delay(email, verify_url)

        # 响应结果
        return http.JsonResponse({'code': '0', 'errmsg': 'ok'})


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # LoginRequiredMixin  封装了是否登录的操作
        # 提供用户中心的页面
        # 判断是否登录
        # if request.user.is_authenticated:
        #     return render(request, 'user_info_center.html')
        # else:
        #     return redirect(reverse('users:login'))
        # 如果LoginRequiredMixin判断用户已经登录，那么request.user就是登录用户登录对象
        content = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }
        return render(request, 'user_info_center.html', content)


class LogoutView(View):
    def get(self, request):
        # 用户退出登录
        # 清除状态保持信息
        logout(request)
        # 响应结果
        # 退出登录后重定向到首页
        response = redirect(reverse('contents:index'))
        # 清除cookie
        response.delete_cookie('username')
        return response


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
        # 为了实现在首页的右上角展示用户信息，我们需要将用户名缓存到cookie中
        # response.set_cookie(key,val,expiry)
        # 响应结果 ,不是一味地重定向到首页，根据从哪来回哪去
        # 先取出next
        next = request.GET.get('next')
        if next:
            # 重定向到next
            response = redirect(next)
        else:
            # 重定向到首页
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', username, max_age=3600 * 24 * 15)
        return response


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
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response
