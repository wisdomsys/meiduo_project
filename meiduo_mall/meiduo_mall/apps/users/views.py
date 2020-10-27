from django.shortcuts import render
from django.views import View


# Create your views here.


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        # 提供用户注册页面
        return render(request, 'register.html')

    def psot(self,request):
        # 实现用户注册逻辑
        # 接收参数
        value = request.POST.get('key')
        pass

        # 校验参数
        # 保存注册数据
        # 响应结果