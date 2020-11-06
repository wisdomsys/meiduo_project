import logging
import random
from django import http
from django.views import View
from django_redis import get_redis_connection

from verifications.libs.captcha.captcha import captcha
from . import constants
from celery_tasks.sms.tasks import send_sms_code

# Create your views here.

logger = logging.getLogger('django')


# class CheckSMSCodeView(View):
#     # test用
#     def get(self, request, mobile):
#         sms_code_client = request.GET.get('sms_code')
#         redis_conn = get_redis_connection('sms_code')
#         sms_code_server = redis_conn.get('sms_%s' % mobile).decode()
#         if not all([mobile, sms_code_client]):
#             return http.JsonResponse('缺少必要参数')
#         if sms_code_server is None:
#             return http.JsonResponse({'code': '60001', 'errmsg': '未查询到获取短信验证码'})
#         if sms_code_client != sms_code_server:
#             return http.JsonResponse({'code': '60001', 'errmsg': '输入的短信验证码错误'})
#         else:
#             return http.JsonResponse({'code': '0', 'msg': 'ok'})


class ImageCodeView(View):
    # 图形验证码
    def get(self, request, uuid):
        # parm 通用唯一识别码，用于标识是哪个用户的
        # 接收参数 校验参数
        # 实现主体业务逻辑：生成、保存、响应图像验证码
        # 生成
        text, image = captcha.generate_captcha()

        # 保存
        redis_conn = get_redis_connection('verify_code')
        # redis_conn.setex('key','expires','value')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应结果
        return http.HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    def get(self, request, mobile):
        # 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 校验参数
        if not all([image_code_client, uuid]):
            return http.HttpResponse('缺少必要参数')

        # 判断用户是否频繁发送短信验证码
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': '60002', 'errmsg': '发送短信频繁'})

        # 提取图像验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code': '4001', 'errmsg': '图形验证码已失效'})

        # 删除图形验证码,防止恶意测试
        redis_conn.delete('img_%s' % uuid)
        # 对比图像验证码
        # 将bytes转成字符串再比较
        image_code_server = image_code_server.decode()
        if image_code_client.lower() != image_code_server.lower():  # 转小写 再比较
            return http.JsonResponse({'code': '4001', 'errmsg': '输入图形验证码有误'})

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)  # 手动输出日志 记录短信验证码

        # 保存短信验证码
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # # 保存发送验证码的标记
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        # 创建redis管道

        pl = redis_conn.pipeline()
        # 将命令添加到队列中
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, 60, 1)
        # 执行
        pl.execute()

        # 发送短信验证码 - 使用celery
        # send_sms_code(mobile, sms_code) 错误的写法
        send_sms_code.delay(mobile, sms_code)   # 不要忘记写delay，固定的写法

        # 响应
        return http.JsonResponse({'code': '5000', 'sms_code': sms_code})
        # return http.JsonResponse({'code': '50000', 'errmsg': '发送短信成功'})
