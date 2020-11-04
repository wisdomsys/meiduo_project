# 定义任务
from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.main import celery_app


# 使用装饰器装饰异步任务，保证celery识别任务
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    # 发送短信验证码的异步任务
    send_ret = CCP().send_template_sms(mobile, [sms_code, 300 // 60], 1)
    return send_ret

