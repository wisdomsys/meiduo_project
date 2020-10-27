# 编写jinjia2模板引擎
from jinja2 import Environment
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage


def jinja2_environment(**options):
    # 创建环境对象
    env = Environment(**options)
    # 自定义语法： {{ static('静态文件相对路径')}} {{url('路由的命名空间')}}
    env.globals.update({
        'static': staticfiles_storage.url,  # 获取静态文件的前缀
        'url': reverse,  # 反向解析，重定向
    })

    # 返回环境对象
    return env
