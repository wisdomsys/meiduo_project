// 创建vue对象
// 采用的是es6语法
let vm = new Vue({
    el:'#app',  //
    delimiters:['[[',']]'],
    data:{// 数据对象
        //v-model
        username:'',
        password:'',
        password2:'',
        mobile:'',
        image_code:'',
        sms_code:'',
        allow:'',

        // v-show
        error_name : false,
        error_password:false,
        error_password2:false,
        error_mobile: false,
        error_image_code:false,
        error_sms_code:false,
        error_allow:false,

        // error_massage
        error_name_message:'',
        error_mobile_message:'',

    },
    methods:{// 定义和实现事件方法
        // 校验用户名
        check_username(){
            // 用户名5-20个字符[a-zA-Z0-9_-]
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if(re.test(this.username)){
                // 匹配成功，不展示错误信息
                this.erroe_name = false;
            }else {
                //匹配失败，展示错误信息
                this.error_name_message = '请输入5-20个字符的用户名'
                this.error_name = true;
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
                this.error_mobile_message = '请输入正确的手机号'
                this.error_mobile = true
            }
        },
        check_image_code(){},
        check_sms_code(){},
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
            if (this.erroe_name == true || this.error_password == true||this.error_password2==true||this.error_allow==true||this.error_mobile==true){
                // window.event.returnValue =false;
                window.event.preventDefault();
                // return false
            }

        },
        generate_image_code(){},
        send_sms_code(){},
    }
});