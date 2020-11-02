// 创建vue对象
// 采用的是es6语法

let vm = new Vue({
    el:'#app',  //
    delimiters:['[[',']]'],
    data: {// 数据对象
        //v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        image_code: '',
        image_code_url: '',
        sms_code: '',
        allow: '',
        uuid: '',
        sms_code_tip:'获取短信验证码',
        send_flag:false,

        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_image_code: false,
        error_sms_code: false,
        error_allow: false,

        // error_massage
        error_name_message: '',
        error_mobile_message: '',
        error_image_code_message:'',
        error_sms_code_message:'',
    },

    // mounted(){ //页面加载完会被调用的
    //     // 生成图形验证码
    //     //     this.uuid = generateUUID();
    //     //     this.image_code_url = '/image_codes/'+this.uuid+'/';
    //     //     alert(this.image_code_url)
    //     this.generate_image_code();
    // },
    mounted(){
        this.uuid = generateUUID();
        this.image_code_url = '/image_codes/'+this.uuid+'/';
        // this.generate_image_code();
    },
    methods:{// 定义和实现事件方法
        //生成图形验证码的方法:封装的思想、代码的复用
        generate_image_code(){
            this.uuid = generateUUID();
            this.image_code_url = '/image_codes/'+this.uuid+'/';
        },
        // 校验用户名
        check_username(){
            // 用户名5-20个字符[a-zA-Z0-9_-]
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if(re.test(this.username)){
                // 匹配成功，不展示错误信息
                this.erroe_name = false;
            }else {
                //匹配失败，展示错误信息
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            // 判断注册的用户名是否重复
            // axios.get('url','请求头')
                // .then(function (response) {
                    //
                    // })
                    // .catch(function (error) {
                    //
                    // })
            if (this.erroe_name==false){
                // 只有当用户输入的用户名满足条件时，才会发送请求
                // es6语法
                let url = '/username/'+this.username+'/count/';
                axios.get(url,{
                    responseType:'json'
                })
                    .then(response=>{
                        if (response.data.count==1){
                            // 用户名已存在
                            this.error_name_message='用户名已存在'
                            this.error_name=true
                        }else{
                            // 用户名不存在
                            this.error_name = false
                        }
                    })
                    .catch(error=>{
                        console.log(error.response)
                    })
            }
        },
        // 校验密码
        check_pwd(){
            let re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)){
                this.error_password = false
            }else {
                this.error_password=true
            }
        },
        // 校验两次输入的密码是否一致
        check_pwd2(){
            if (this.password === this.password2){
                this.error_password2 = false
            }else {
                this.error_password2 = true
            }
        },
        // 校验手机号是否正确
        check_mobile(){
            let re =/^1[0-9]{10}$/;
            if (re.test(this.mobile)){
                this.error_mobile = false
            }else {
                this.error_mobile_message = '请输入正确的手机号';
                this.error_mobile = true
            }
            if (this.error_mobile==false){
                let url = '/mobile/'+this.mobile+'/count/';
                axios.get(url,{
                    responseType: 'json'
                })
                    .then(response=>{
                        if (response.data.count==1){
                            // 手机号已经存在
                            this.error_mobile_message = '手机号已存在';
                            this.error_mobile=true
                        }else{
                            this.error_mobile=false
                        }
                    })
                    .catch(error=>{
                        console.log(error.response)
                    })
            }
        },

        // 校验图形验证码
        check_image_code(){
            if (this.image_code.length !=4){
                this.error_image_code_message = '请输入图形验证码';
                this.error_image_code = true;
            }else {
                this.error_image_code = false;
            }
        },
        // 发送短信和校验图形验证码
        send_sms_code(){
            //避免恶意用户频繁的点击获取验证码
            if (this.send_flag == true){
                return;
            }
            this.send_flag = true;
            if(this.error_image_code ===true || this.error_mobile===true){
                this.send_flag = false;
                return;
            }
            this.send_flag = true;

            let url = '/sms_codes/'+this.mobile+'/?image_code='+this.image_code+'&uuid='+this.uuid;
            axios.get(url,{
                responseType:'json',
            })
                .then(response=>{
                    if (response.data.code=='5000'){
                        // 展示60s倒计时 + 短信验证码
                        let num = 60;
                        let t = setInterval(()=>{
                            if (num==1){
                                // 停止回调函数的执行
                                clearInterval(t);
                                // 还原sms_code_tip的提示文字
                                this.sms_code_tip = '获取短信验证码';
                                // 重新生成图形验证码
                                this.generate_image_code();
                                this.send_flag = false;
                            }else {
                                num-=1;
                                this.sms_code_tip = num+'秒/'+response.data.sms_code;
                            }
                        },1000)
                    }else {
                        // 其他两种情况  图形验证码过期 图形验证码错误
                        if (response.data.code='4001') {
                            this.error_image_code_message = response.data.errmsg;
                            this.error_image_code = true;
                            this.send_flag = false;
                        }else{
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true;
                        }
                    }

                })
                .catch(error=>{
                    console.log(error.response)
                    this.send_flag = false;
                })
        },

        // 校验短信验证码
        check_sms_code(){
            if (this.sms_code.length !=6){
                this.error_sms_code_message = '请输入正确的短信验证码';
                this.error_sms_code = true;
            }else {
                this.error_sms_code_message = false;
            }
            // test用的
            // let url = '/check_sms_code/'+this.mobile+'/?sms_code='+this.sms_code;
            // axios.get(url,{
            //     responseType:'json',
            // })
            //     .then(response=>{
            //         if (response.data.code == '60001'){
            //             this.error_sms_code_message = response.data.errmsg;
            //             this.error_sms_code = true
            //         }
            //     })
            //     .catch(error=>{
            //         console.log(error.response)
            //     })
        },

        // 检查是否勾选协议
        check_allow(){
            if (!this.allow){
                this.error_allow = true
            }else {
                this.error_allow =false;
            }
        },
        // 监听表单提交事件
        on_submit(){
            this.check_username();
            this.check_pwd();
            this.check_pwd2();
            this.check_mobile();
            this.check_allow();
            this.check_sms_code();
            if (this.erroe_name == true || this.error_password == true||this.error_password2===true||this.error_mobile==true||this.error_image_code==true||this.error_sms_code==true||this.error_allow==true){
                // window.event.returnValue =false;
                // window.event.preventDefault();
                return false
            }
        },
    },
});