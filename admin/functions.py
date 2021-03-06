from django.shortcuts import render, redirect
from admin import views
# Create your views here.

from django.http import HttpResponse, Http404, JsonResponse
from website.models import *
from django.core.serializers import serialize
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
import re
import json
from django.core.serializers.json import DjangoJSONEncoder
import pandas as pd
from datetime import datetime
from datetime import timedelta
from sender import Mail, Message

def check_rule(request):
    if 'user' in request.session:
        user = request.session.get('user')
        print(user['role'])
        if 0 in user['role']:
            print(user)
            return 1
        return 0
    return 0

# Phuc doc tham khao Service

def services(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            services = []
            service_all = Service.objects.all()
            for item in service_all:
                service = []
                service.append('<a href="/admin/service/edit/'+ str(item.id) +'">'+ str(item.service_name) +'</a>')
                service.append(str(item.value) + ' tin')
                service.append(str(item.day_limit)+ ' ngày')
                service.append(str(item.amount)+ ' VNĐ')
                if item.is_active == True:
                    service.append('<b style="color:green">Đang bán</b>')
                else:
                    service.append('<b style="color:red">Ngưng bán</b>')
                services.append(service)
            return HttpResponse(json.dumps(services), content_type="application/json")
        return HttpResponse(serialize('json', Service.objects.all()), content_type="application/json")
    return HttpResponse('Error')


# Service_add
@csrf_exempt    
def service_add(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        print(request.POST)
        service_name = request.POST.get('inputServiceName')
        amount = request.POST.get('inputAmount')
        value = request.POST.get('inputValue')
        quantity_product = request.POST.get('inputQuantityProduct')
        day_limit = request.POST.get('inputDayLimit')
        visable_vip = request.POST.get('inputVisableVip')
        is_active = request.POST.get('inputIsActive')

        service = Service(
            service_name=service_name,
            amount=amount,
            value=value,
            quantity_product=quantity_product,
            day_limit=day_limit,
            visable_vip=visable_vip,
            is_active=is_active,
            creator_id=request.session.get('user')['id'],
        )
        service.save()
        accounts = Account.objects.filter(activity_merchant=True)
        for item in accounts:
            Account_Service.objects.create(
                account = item,
                service = service,
            )
        return HttpResponse(1)
    return HttpResponse('Lỗi hệ thống!\n Chúng tôi sẽ khắc phục sớm')

@csrf_exempt  
def service(request, id_service):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        service = Service.objects.get(pk=id_service).__dict__
        del service['_state']
        account = Account.objects.filter(pk=service['creator_id']).values('email')
        
        service['account'] = account[0]
        return HttpResponse(json.dumps(service, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
    if request.method == 'POST':
        try:
            is_active = request.POST.get('inputIsActive')
            service = Service.objects.get(id=id_service)
            service.is_active = is_active
            service.save()
            return HttpResponse(1)
        except:
            return HttpResponse(0)
    if request.method == 'DETELE':

        service = Service.objects.get(id=id_service)
        service.is_active = False
        service.save()
        return HttpResponse(1)

    return HttpResponse(0)

# ket thuc tham khao


# Code Category va Attribute dua theo Serive ben duoc comment nay
# Viet funtion nho viet URL va views
def categories(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        categories = []
        categories_all = Category.objects.all()
        for item in categories_all:
            category = []
            category.append('<a href="/admin/category/edit/'+ str(item.id) +'">'+ str(item.id) +'</a>'),
            category.append('<a href="/admin/category/edit/'+ str(item.id) +'">'+ str(item.name_category) +'</a>'),         
            category.append(str(item.quantity))
            if item.is_active == True:
                category.append('<b style="color:green">Kích hoạt</b>')
            else:
                category.append('<b style="color:red">Đang khoá</b>')
            categories.append(category)
        return HttpResponse(json.dumps(categories), content_type="application/json")
    return HttpResponse('error')


@csrf_exempt    
def category_add(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if check_rule(request) == 0:
        return HttpResponse('Error')

    if request.method == 'POST':
        print(request.POST)
        name_category = request.POST.get('inputName')
        #try:
        category = Category(
            name_category = name_category,
        )
        category.save()
        return HttpResponse(1)
        # except :
        #     return HttpResponse(0)
        return HttpResponse('Check')
    return HttpResponse('Error Add Category!')

@csrf_exempt  
def category(request, id_category):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        return HttpResponse(serialize('json', Category.objects.filter(pk=id_category)), content_type="application/json")
    if request.method == 'POST':
        try:
            name_category = request.POST.get('inputName')
            is_active = request.POST.get('inputIsActive')
            category = Category.objects.get(id=id_category)
            category.name_category = name_category
            category.is_active = is_active
            category.save()
        
            if category.is_active == '0': #Khoá
                Product_Category.objects.filter(category_id=category,archive=False).update(archive=True,lock=True)
            else: #Kich hoat   
                Product_Category.objects.filter(category_id=category,lock=True).update(archive=False,lock=False)
           
            
            return HttpResponse(1)
        except:
            return HttpResponse(0)
    if request.method == 'DETELE':
        category = Category.objects.get(id=id_category)
        category.is_active = False
        category.save()
        Product_Category.objects.filter(category_id=id_category,archive=False).update(archive=True,lock=True)

        return HttpResponse(1)

    return HttpResponse(0)



######
######
###### Attribute
######
######
######
######


def attributes(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        attributes = []
        attributes_all = Attribute.objects.all()
        for item in attributes_all:
            attribute = []
            attribute.append('<a href="/admin/attribute/edit/'+ str(item.id) +'">'+ str(item.label) +'</a>'),         
            if item.is_active == True:
                attribute.append('<b style="color:green">Có</b>')
            else:
                attribute.append('<b style="color:red">Không</b>')

            attributes.append(attribute)
        return HttpResponse(json.dumps(attributes), content_type="application/json")
    return HttpResponse('error')

@csrf_exempt    
def attribute_add(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'POST':
        print(request.POST)
        label = request.POST.get('inputLabel')

        #try:
        attribute = Attribute(
            label = label,
        )
        attribute.save()

        products = Product.objects.filter(type_product=True).values_list('id',flat=True) #id of configure products
        for item in products:
            versions = Link_Type.objects.filter(parent_product=item).values_list('product_id',flat=True) #id of versions of a configure product
            for temp in versions:
                prod_attr = Product_Attribute(
                    product_id=Product.objects.get(id=temp),
                    attribute_id=attribute,
                    value="Chưa cập nhật",
                )
                prod_attr.save()     
        
        return HttpResponse(1)
    return HttpResponse('Lỗi hệ thống!!')

@csrf_exempt  
def attribute(request, id_attribute):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        return HttpResponse(serialize('json', Attribute.objects.filter(pk=id_attribute)), content_type="application/json")
    if request.method == 'POST':
        try:
            label = request.POST.get('inputLabel')
            is_active = request.POST.get('inputIsActive')

            attribute = Attribute.objects.get(id=id_attribute)
            attribute.label = label
            attribute.is_active = is_active
            attribute.save()

            if attribute.is_active == '0': #Khoá
                Product_Attribute.objects.filter(attribute_id=id_attribute,archive=False).update(archive=True,lock=True)
            else: #Kich hoat
                Product_Attribute.objects.filter(attribute_id=id_attribute,lock=True).update(archive=False,lock=False)
            
            return HttpResponse(1)
        except:
            return HttpResponse(0)

    if request.method == 'DETELE':
        attribute = Attribute.objects.get(id=id_attribute)
        attribute.is_active = False
        attribute.save()
        Product_Attribute.objects.filter(attribute_id=id_attribute,archive=False).update(archive=True,lock=True)

        return HttpResponse(1)

    return HttpResponse(0)


####  
####
####
####
####    Account
####
####
####
####

@csrf_exempt
def user(request, id_user):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        if Account.objects.filter(pk=id_user, is_admin=False).exists() == True:
            user = Account.objects.get(pk=id_user)
            account = dict()
            account['username']  = user.username
            account['email'] = user.email
            account['name_shop'] = user.name_shop
            account['name']  = user.name
            account['phone'] = user.phone
            account['id_card'] = user.id_card
            account['address'] = user.address
            account['birthday'] = user.birthday

            if user.activity_merchant == True:
                account['role'] = 2
            if user.activity_advertiser == True:
                account['role'] = 3
            if user.activity_account and user.activity_merchant == False and user.activity_advertiser == False:
                account['role'] = 1
            if user.is_admin == True:
                account['role'] = 0

            account['lock'] = user.is_lock
            account['sex'] = user.sex

            return HttpResponse(json.dumps(account), content_type="application/json")
        else:
            return HttpResponse(-3)

    #mo khoa tai khoan
    if request.method == 'POST':
        if Account.objects.filter(pk=id_user, is_admin=False).exists() == False:
            return HttpResponse('Tài khoản không tồn tại')
        account = Account.objects.get(pk=id_user)
        account.is_lock = True
        account.save()
        return HttpResponse(1)
    # khoa tai khoan
    if request.method == 'DELETE':
        if Account.objects.filter(pk=id_user, is_admin=False).exists() == False:
            return HttpResponse('Tài khoản không tồn tại')
        account = Account.objects.get(pk=id_user)
        account.is_lock = False
        account.save()
        return HttpResponse(1)
    return HttpResponse(-1)


def users(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
        
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            users = []
            user_all = Account.objects.filter(is_admin=False)
            for item in user_all:
                user = []
                user.append('<a href="/admin/user/see/'+ str(item.id) +'">'+ item.email +'</a>')
                user.append(item.name)
                if item.activity_merchant == True:
                    user.append('Người bán')
                    count_star = Rating.objects.filter(merchant_id=item.id).aggregate(Sum('num_of_star'))['num_of_star__sum']
                    count_person = Rating.objects.filter(merchant_id=item.id, is_activity=True).count()
                    if count_star == None:
                        user.append('0 <i class="fa fa-star"></i>' + '/ ' + str(count_person) + ' đánh giá')
                    else:
                        user.append(str(count_star) + ' <i class="fa fa-star"></i>' + '/ ' + str(count_person) + ' đánh giá')
                elif item.activity_advertiser == True:
                    user.append('Người quảng cáo')
                    user.append('Không có đánh giá')
                elif item.activity_account == True and item.activity_merchant == False:
                    user.append('Người mua')
                    count_star = Rating_Customer.objects.filter(customer_id=item.id).aggregate(Sum('num_of_star'))['num_of_star__sum']
                    count_person = Rating_Customer.objects.filter(customer_id=item.id, is_activity=True).count()
                    if count_star == None:
                        user.append('0 <i class="fa fa-star"></i>' + '/ ' + str(count_person) + ' đánh giá')
                    else:
                        user.append(str(count_star) + ' <i class="fa fa-star"></i>' + '/ ' + str(count_person) + ' đánh giá')
                
                
                if item.is_lock == True:
                    user.append('<label class="label label-danger">Đã bị khóa</label>')
                else:
                    if item.activity_merchant == False and item.activity_advertiser == False and item.activity_account == False:
                        user.append('<label class="label label-warning">Không hoạt động</label>')
                    else:
                        user.append('<label class="label label-success">Đang hoạt động</label>')
                users.append(user)
            return HttpResponse(json.dumps(users), content_type="application/json")
        return HttpResponse(503)
    return HttpResponse(404)
        

#### Account service

def account_services(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        if request.GET.get('service') == 'available':
            if request.GET.get('table') == 'true':
                list_acc_ser = []
                account_services = Account_Service.objects.filter(account__id=request.session.get('user')['id'], remain__gt=0)
                for item in account_services:
                    acc_ser = []
                    acc_ser.append('<a href="/merchant/purchase_service/'+ str(item.service_id) +'"> TD'+ str(item.service_id) +'</a>')
                    acc_ser.append(item.service.service_name)
                    acc_ser.append(str(item.remain)+ ' tin')
                    acc_ser.append(str(item.service.day_limit) + ' ngày')
                    list_acc_ser.append(acc_ser)
                return HttpResponse(json.dumps(list_acc_ser), content_type="application/json")

            account_services = Account_Service.objects.filter(account__id=request.session.get('user')['id'], remain__gt=0)
            list_account_service = []
            for account_service in account_services:
                dict_account_service = dict()
                dict_account_service['post_id'] = account_service.pk
                dict_account_service['account_id'] = account_service.account_id
                dict_account_service['service_id'] = account_service.service_id
                dict_account_service['service_name'] = Service.objects.get(pk=account_service.service_id).service_name
                dict_account_service['remain'] = account_service.remain
                list_account_service.append(dict_account_service)
            return HttpResponse(json.dumps(list_account_service), content_type="application/json")
    return HttpResponse('Error')


######
######
######
######  Prdouct
######
######
######


def products(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            products = []
            prod_all = Product.objects.filter(type_product=True).order_by('-pk')
            for item in prod_all:
                if Link_Type.objects.filter(parent_product=item.id).exists() == True:
                    product = []
                    product.append('<a href="/admin/product/see/'+ str(item.id) +'">SP'+ str(item.id) +'</a>')
                    product.append(item.name)
                    product.append(str(item.price) + ' VND')
                    image = Product_Image.objects.filter(product_id_id=item.id, archive=False).order_by('image_id_id').first()
                    product.append('<div class="tbl_thumb_product"><img src="/product/' + image.image_id.image_link.url + '" /></div>')
                    if item.archive == 0:
                        if item.is_activity == 1:
                            product.append('<p style="color:green">Được hiển thị</p>')
                        if item.is_activity == 0:
                            product.append('<p style="color:red">Bị khóa</p>')
                    elif item.archive == 1:
                        product.append('<p style="color:blue">Đã xóa</p>') 
                    products.append(product)
            return HttpResponse(json.dumps(products), content_type="application/json")
    return

@csrf_exempt  
def product(request, id_product):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')

    if request.method == 'GET':
        if Product.objects.filter(pk=id_product).exists() == False:
            return HttpResponse('Sản phẩm không tồn tại')

        product = Product.objects.get(pk=id_product).__dict__
        del product['_state']
        product_category = Product_Category.objects.filter(product_id=int(id_product), archive=False)
        list_category = []
        for item in product_category:
            category = Category.objects.get(pk=item.category_id_id).__dict__
            del category['_state']
            list_category.append(category)
        product['categories'] = list_category

        product_image = Product_Image.objects.filter(product_id=int(id_product), archive=False).order_by('image_id_id')
        list_image = []
        for item in product_image:
            image = Image.objects.get(pk=item.image_id_id).__dict__
            del image['_state']
            list_image.append(image)
        product['images'] = list_image

        tags = Tag.objects.filter(tag_type=1, tag_value=product['id'], archive=False)
        list_tag = []
        for item in tags:
            tag = item.__dict__
            del tag['_state']
            list_tag.append(tag)
        product['tags'] = list_tag

        #lay ra danh sach phien ban
        link_type = Link_Type.objects.filter(parent_product=int(id_product), product_id__archive=False)
        list_attr = []
        list_price = []
        for item in link_type:
            list_tmp = []
            list_price.append(item.product_id.price)
            product_attr = Product_Attribute.objects.filter(product_id=item.product_id.id).order_by('attribute_id')
            for item in product_attr:
                list_tmp.append(item.value)
            list_attr.append(list_tmp)
    
        #su dung matrix de tra ve danh sach gia tri cho tung thuoc tinh
        len_atr = len(list_attr[0])
        len_verison = len(list_attr)
        list_value_attr = []
        for i in range(len_atr):
            list_temp = []
            for j in range(len_verison):
                if list_attr[j][i] not in list_temp:
                    list_temp.append(list_attr[j][i])
            list_value_attr.append(list_temp)

        product['list_attr'] = list_value_attr
        product['list_price'] = list_price
        product['price_max_min'] = [max(list_price), min(list_price)]

        return  HttpResponse(json.dumps(product, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")

    #check role
    # Khoa san pham
    # Khong cho mo khoa san pham
    if request.method == 'POST':
        if Product.objects.filter(pk=id_product).exists() == False:
            return HttpResponse('Sản phẩm không tồn tại')
        product = Product.objects.get(pk=id_product)
        if product.is_activity == False:
            return HttpResponse('Sản phẩm đã bị khóa')
        if product.archive == True:
            return HttpResponse('Sản phẩm đã bị xóa')
        if Post_Product.objects.filter(product_id_id=product.id, is_lock=False).exists() == True:
            Post_Product.objects.filter(product_id_id=product.id, is_lock=False).update(is_lock=True)
        product.is_activity=False
        product.save()
        html = '<p>Sản phẩm "'+ product.name +'" của bạn đã bị khóa vì vi phạm các điều kiện của chúng tôi.</p>'
        html +='<p>Mọi thắc mắc xin vui lòng liên hệ với chúng tôi để được giải đáp</p>'
        send_email_notifile(product.account_created.email, 'Sản phẩm của bạn đã bị khóa', html)
        return HttpResponse(1)
    return        
        
####  POST

def posts(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        posts = []
        post_all = Post_Product.objects.all()
        for item in post_all:
            post = []
            post.append('<a href="/admin/post/edit/'+ str(item.id) +'"> TD'+ str(item.id) +'</a>')
            post.append('<a href="/admin/user/see/'+ str(item.creator_id.id) +'">'+ str(item.creator_id.name) +'</a>')
            post.append(item.quantity - item.bought)
            post.append(item.expire.replace(tzinfo=None).strftime("%d/%m/%Y %H:%M"))
            post.append(item.post_type.service_name)
            if item.is_lock == False:
                if item.is_activity == True:
                    post.append('<label class="label label-success">Đang hiển thị</label>')
                else:
                    post.append('<label class="label label-info">Ngừng hiển thị</label>')
            else:
                if item.expire.replace(tzinfo=None) <= datetime.now():
                    post.append('<label class="label label-warning">Hết hạn</label>')
                else: 
                    post.append('<label class="label label-danger">Bị khóa</label>')
            posts.append(post)
        return HttpResponse(json.dumps(posts), content_type="application/json")
    return HttpResponse('error')

#### payment

### Ly Thanh 
#Servies Ads Ly Thanh

@csrf_exempt
def getAllPostAds(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        result = []
        for item in Service_Ads_Post.objects.filter(purchase_service_id__state=2,state=1):
            post_dict = dict()
            post_dict['id'] = item.id
            post_dict['ads_name'] = "<a href='/admin/manager_ads/register_detail/"+str(item.purchase_service_id.id)+"'>"+item.service_name+"</a>"
            post_dict['user'] = item.customer_id.name
            post_dict['date_start']=item.purchase_service_id.date_start.replace(tzinfo=None).strftime("%d/%m/%Y")
            post_dict['position'] = item.purchase_service_id.service_ads_id.position
            post_dict['status'] = "<label class='label label-warning'>Đang chờ</label>"
            result.append(post_dict)
        if result:
            return HttpResponse(json.dumps(result),content_type="application/json")
    
    return HttpResponse(-1)

@csrf_exempt
def getAllAds(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')     
    if request.method == 'GET':
        ads = []
        for item in Service_Ads.objects.all():
            ads_dict = dict()
            ads_dict['service_name'] = "<a href='/admin/manager_ads_detail/"+str(item.pk)+"'>"+item.service_name+"</a>"
            ads_dict['position'] = item.position
            ads_dict['amount'] = item.amount
            ads_dict['day_limit'] = item.day_limit
            if item.is_active:
                ads_dict['is_active'] = "<label class='label label-info'>Kích hoạt</label>"
            else:
                ads_dict['is_active'] = "<label class='label label-warning'>Bị khóa</label>"
            ads.append(ads_dict)
        return  HttpResponse(json.dumps(ads), content_type="application/json")
    return  HttpResponse(1)

@csrf_exempt
def AddService(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        _is_active = False
        if request.POST.get('inputStatus') == "Kích hoạt":
            _is_active = True
        _amount = int(request.POST.get('inputAmount').replace(',', ''))
        _date = int(re.sub('\D','',request.POST.get('inpuLimit')))
        obj, created = Service_Ads.objects.update_or_create(
            id = request.POST.get('inputId'),
            defaults = {
                'service_name' : request.POST.get('inputName'),
                'position' : request.POST.get('inputPosition'),
                'amount' : _amount,
                'day_limit' : _date,
                'is_active' : _is_active,
                'creator_id' : 1,
            }
        )
        ads = Service_Ads.objects.filter(service_name=request.POST.get('inputName')).first()
        if ads is None:
            return render(request,'admin/manager_ads/manager_ads_detail.html',{'error':error})
    success = "success"
    return render(request,'admin/manager_ads/manager_ads_detail.html',{'success':success,'ads':obj})

def RemoveService(request,id):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    ads = Service_Ads.objects.filter(id=id).first()
    if ads is None:
        error = "error"
        return render(request,'admin/manager_ads/manager_ads_detail.html',{'error':error})
    else:
        ads.delete()
    success = "success"
    return render(request,'admin/manager_ads/manager_ads.html',{'success':success})

import pytz

@csrf_exempt
def getAllAdsActiving(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    input = Purchase_Service_Ads.objects.filter(state=4,is_active=True)
    result = []
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    # now = pytz.utc.localize(now)
    for item in input:
        if item.date_start<=now and now<item.date_start+timedelta(days=item.service_ads_id.day_limit):
            ads_dict = dict()
            ads_dict['id'] = item.id
            ads_dict['end'] = (item.date_start+timedelta(days=item.service_ads_id.day_limit)).strftime('%Y-%m-%d-%H-%M-%S')
            #ads_dict['start'] = (item.date_start).strftime('%m-%d-%Y-%H-%M-%S')
            result.append(ads_dict)
    for item in Purchase_Service_Ads.objects.filter(state=3,is_active=True):
        ads_dict = dict()
        ads_dict['id']= "start_"+str(item.id)
        ads_dict['end']=(item.date_start).strftime('%Y-%m-%d-%H-%M-%S')
        result.append(ads_dict)
    if len(result) < 6:
        arr_chose = []
        arr_chose.append("Đầu trang")
        arr_chose.append("Giữa trang")
        arr_chose.append("Cuối trang")
        arr_chose.append("Slide")
        arr_chose.append("Bên phải slide 1")
        arr_chose.append("Bên phải slide 2")
        check = []
        for i in range(6):
            check_dict = dict()
            check_dict['check']=False
            check_dict['key'] = arr_chose[i]
            check.append(check_dict)
        for item in input:
            for i in range(6):
                if item.service_ads_id.position == check[i]['key']:
                    check[i]['check']=True
        for item in check:
            if item['check'] == False:
                ads_dict = dict()
                ads_dict['id']="none_"+item['key']
                ads_dict['end']=(now+timedelta(minutes=30)).strftime('%m-%d-%Y-%H-%M-%S')
                result.append(ads_dict) 
    if result:
        return HttpResponse(json.dumps(result),content_type="application/json")
    return HttpResponse(-1)

@csrf_exempt
def enable_ads(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id = request.POST['inputID']
        service_ads = Purchase_Service_Ads.objects.filter(id=id)
        service_ads.update(state=4)
        return HttpResponse(1)
    return HttpResponse(-1)
@csrf_exempt
def disable_ads(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id = request.POST['inputID']
        service_ads = Purchase_Service_Ads.objects.filter(id=id)
        service_ads.update(state=5)
        return HttpResponse(1)
    return HttpResponse(-1)

@csrf_exempt
def getDetailRegister(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id = request.POST['inputID']
        post_ads = Service_Ads_Post.objects.filter(purchase_service_id__id=id,state=1,purchase_service_id__state=2).first()
        if post_ads:
            post_dict = dict()
            post_dict['id']=post_ads.id
            post_dict['img_1'] = post_ads.image_1
            post_dict['content_1']= post_ads.image_1_content
            post_dict['url_1']=post_ads.image_1_url
            post_dict['img_2'] = post_ads.image_2
            post_dict['content_2']= post_ads.image_2_content
            post_dict['url_2']=post_ads.image_2_url
            post_dict['img_3'] = post_ads.image_3
            post_dict['content_3']= post_ads.image_3_content
            post_dict['url_3']=post_ads.image_3_url
            return HttpResponse(json.dumps(post_dict),content_type="application/json")
    return HttpResponse(-1)

@csrf_exempt
def confirmPost(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        sid = request.POST['inputSID']
        pid = request.POST['inputPID']
        service_ads = Purchase_Service_Ads.objects.filter(id=sid)
        service_ads.update(state=3)
        post_ads = Service_Ads_Post.objects.filter(id=pid)
        post_ads.update(state=2)
        body ="Thông báo duyệt nội dung quảng cáo"
        content = "<html><body>"
        content += "<h2 style='text-align:center;'>Nội dung quảng cáo của bạn đã được duyệt</h2>"
        content += "<br><label style='font-size:14px'>Nội dung quảng cáo</label>"
        content += "<img src='http://localhost:8000/ads/"+post_ads[0].image_1+"'>"
        content += "<br><br> <b>Nếu có thắc mắc, vui lòng liên hệ chúng tôi trong vòng 48h - kể từ lúc mail này được gửi."
        content+=  "Mọi sự cố liên quan đến giao dịch quá thời hạn trên chúng tôi sẽ không giải quyết, xin cám ơn. </b> "
        content+="</body></html>"
        send_email_notifile(service_ads[0].merchant_id.email,body,content)
        return HttpResponse(1)
    return HttpResponse(-1)
@csrf_exempt
def cancelPost(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        sid = request.POST['inputSID']
        pid = request.POST['inputPID']
        service_ads = Purchase_Service_Ads.objects.filter(id=sid)
        service_ads.update(state=1)
        post_ads = Service_Ads_Post.objects.filter(id=pid)
        post_ads.update(state=0)
        body ="Thông báo duyệt nội dung quảng cáo"
        content = "<html><body>"
        content += "<h2 style='text-align:center;'>Nội dung quảng cáo của bạn <b> không được duyệt </b></h2>"
        content += "<br><label style='font-size:14px'>Nội dung quảng cáo</label>"
        content += "<img src='http://localhost:8000/ads/"+post_ads[0].image_1+"'>"
        content += " <br><br> <b>Nếu có thắc mắc, vui lòng liên hệ chúng tôi. Hotline: 0978956043 - Mail: abc@gmail.com"
        content+="</body></html>"
        send_email_notifile(service_ads[0].merchant_id.email,body,content)
        return HttpResponse(1)
    return HttpResponse(-1)

@csrf_exempt
def getAllAdsRunning(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        result = []
        for item in Service_Ads_Post.objects.filter(purchase_service_id__state=4,state=2):
            post_dict = dict()
            post_dict['id'] = item.id
            post_dict['ads_name'] = "<a href='/admin/manager_ads_running_detail/"+str(item.purchase_service_id.id)+"'>"+item.service_name+"</a>"
            post_dict['user'] = item.customer_id.name
            post_dict['date_start']=item.purchase_service_id.date_start.replace(tzinfo=None).strftime("%d/%m/%Y")
            post_dict['date_end'] = (item.purchase_service_id.date_start+timedelta(days=item.purchase_service_id.service_ads_id.day_limit)).replace(tzinfo=None).strftime("%d/%m/%Y")
            post_dict['status'] = "<label class='label label-warning'>Đang chạy</label>"
            result.append(post_dict)
        if result:
            return HttpResponse(json.dumps(result),content_type="application/json")
    
    return HttpResponse(-1)

@csrf_exempt
def getDetailRunning(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id = request.POST['inputID']
        post_ads = Service_Ads_Post.objects.filter(purchase_service_id__id=id,state=2,purchase_service_id__state=4).first()
        if post_ads:
            post_dict = dict()
            post_dict['id']=post_ads.id
            post_dict['img_1'] = post_ads.image_1
            post_dict['content_1']= post_ads.image_1_content
            post_dict['url_1']=post_ads.image_1_url
            post_dict['img_2'] = post_ads.image_2
            post_dict['content_2']= post_ads.image_2_content
            post_dict['url_2']=post_ads.image_2_url
            post_dict['img_3'] = post_ads.image_3
            post_dict['content_3']= post_ads.image_3_content
            post_dict['url_3']=post_ads.image_3_url
            return HttpResponse(json.dumps(post_dict),content_type="application/json")
    return HttpResponse(-1)

### End Ly Thanh


## Order 


def orders(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            list_order = []
            order_all_id = Order_Detail.objects.filter(merchant_id=request.session.get('user')['id']).values_list('order_id').distinct()
            print(order_all_id)
            order_all = Order.objects.filter(pk__in=order_all_id)
            for item in order_all:
                order = []
                order.append('<a href="/admin/manager_order_detail/'+ str(item.id) +'"> DH'+ str(item.id) +'</a>')
                order.append(item.customer.name)
                order.append(str(item.amount) + ' VND')
                order.append(item.created.replace(tzinfo=None))
                order_detail = Order_Detail.objects.filter(order_id=item.id, merchant_id=request.session.get('user')['id']).first()
                if order_detail.state == '1':
                    order.append('<label class="label label-success">Thành công</label>')
                if order_detail.state == '0':
                    order.append('<label class="label label-danger">Hủy bỏ</label>')
                if order_detail.state == '2':
                    order.append('<label class="label label-info">Đặt hàng</label>')
                if order_detail.state == '3':
                    order.append('<label class="label label-warning">Đang gói hàng</label>')
                if order_detail.state == '4':
                    order.append('<label class="label label-default">Đang vận chuyển</label>')
                list_order.append(order)
            return HttpResponse(json.dumps(list_order, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
    return


def order(request, id_order):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if Order_Detail.objects.filter(order_id=id_order, merchant_id=request.session.get('user')['id']).exists() == False:
            return HttpResponse('Đơn hàng không tồn tại!')
        order = Order.objects.get(pk=id_order).__dict__
        customer = Account.objects.get(pk=order['customer_id'])
        order['name_customer'] = customer.name
        rating_count = Rating_Customer.objects.filter(customer_id=order['customer_id']).count()
        rating_ponit = Rating_Customer.objects.filter(customer_id=order['customer_id']).aggregate(Sum('num_of_star'))['num_of_star__sum']
        if rating_ponit == None:
            rating_ponit = 0
        order['rating_count'] = rating_count
        order['rating_point'] = rating_ponit
        del order['_state']
        order_detail = Order_Detail.objects.filter(order_id=id_order, merchant_id=request.session.get('user')['id']).exclude(state__in = [0, 1])
        if order_detail.count() == 0:
            order['rate_cus'] = True
        else:
            order['rate_cus'] = False

        if Rating_Customer.objects.filter(merchant_id=request.session.get('user')['id'], customer_id=customer.id).exists() == True:
            order['disable_rating'] = True
        else:
            order['disable_rating']  = False
        state_now = -1
        for item in order_detail:
            state_now = item.state
            break
        order['state_now'] = state_now
        return HttpResponse(json.dumps(order, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")


def orders_detail(request, id_order):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        list_orders_detail = []
        order_detail_all = Order_Detail.objects.filter(order_id=id_order, merchant_id=request.session.get('user')['id'])
        for item in order_detail_all:
            order_item = []
            product_orgin_id = Link_Type.objects.get(product_id_id=item.product_id).parent_product
            product = Product.objects.get(pk=product_orgin_id)
            image = Product_Image.objects.filter(product_id_id=product_orgin_id, archive=False).order_by('image_id_id').first()
            order_item.append('<a href="/admin/product/see/'+ str(product_orgin_id) +'">'+ product.name +'</a>')
            order_item.append('<div class="tbl_thumb_product"><img src="/product' + image.image_id.image_link.url + '" /></div>')
            price = int(round((item.price * (100 - item.discount))/100, 0))
            order_item.append(str(price) + ' VND')
            order_item.append(str(item.quantity))
            if item.state == '1':
                order_item.append('<label class="label label-success">Thành công</label>')
            if item.state == '0':
                order_item.append('<label class="label label-danger">Hủy bỏ</label>')
            if item.state == '2':
                order_item.append('<label class="label label-info">Đặt hàng</label>')
            if item.state == '3':
                order_item.append('<label class="label label-warning">Đang gói hàng</label>')
            if item.state == '4':
                order_item.append('<label class="label label-default">Đang vận chuyển</label>') 
            list_orders_detail.append(order_item)
        return HttpResponse(json.dumps(list_orders_detail, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")



# Rating


def rating_merchant(request, id_account):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            rating_all = Rating.objects.filter(merchant_id=id_account)
            list_rating = []
            for item in rating_all:
                rating_item = []
                rating_item.append('<a href="/admin/user/see/'+ str(item.customer.id) +'">'+ item.customer.name +'</a>')
                rating_item.append(str(item.num_of_star))
                rating_item.append(item.comment)
                if item.confirm_bought == True:
                    rating_item.append('<label class="label label-success">Đã mua</label>')
                else:
                    rating_item.append('<label class="label label-warning">Chưa mua</label>')
                if item.is_activity == True:
                    rating_item.append('<button onclick="update_rating_mer('+ str(item.id) +', 0)" class="btn btn-danger">Ẩn</button>')
                else:
                    rating_item.append('<button onclick="update_rating_mer('+ str(item.id) +', 1)" class="btn btn-info">Hiển thị</button>')
                list_rating.append(rating_item)
            return HttpResponse(json.dumps(list_rating, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
        return HttpResponse(503)
    return HttpResponse(404)

def rating_customer(request, id_account):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            rating_all = Rating_Customer.objects.filter(customer_id=id_account)
            list_rating = []
            for item in rating_all:
                rating_item = []
                rating_item.append('<a href="/admin/user/see/'+ str(item.merchant.id) +'">'+ item.merchant.name +'</a>')
                rating_item.append(str(item.num_of_star))
                if item.confirm_bought == True:
                    rating_item.append('<label class="label label-success">Đã bán</label>')
                else:
                    rating_item.append('<label class="label label-warning">Chưa bán</label>')
                if item.is_activity == True:
                    rating_item.append('<button onclick="update_rating_cus('+ str(item.id) +', 0)" class="btn btn-danger">Ẩn</button>')
                else:
                    rating_item.append('<button onclick="update_rating_cus('+ str(item.id) +', 1)" class="btn btn-info">Hiển thị</button>')
                list_rating.append(rating_item)
            return HttpResponse(json.dumps(list_rating, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
        return HttpResponse(503)

    return HttpResponse(404)

@csrf_exempt
def update_rating_merchant(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id_rating = request.POST.get('id_rating')
        active_new = request.POST.get('action')
        if Rating.objects.filter(pk=id_rating).exists() == False:
            return HttpResponse('Đánh giá không tồn tại')
        rating = Rating.objects.get(pk=id_rating)
        rating.is_activity = active_new
        rating.save()
        return HttpResponse(1)
    return HttpResponse(503)

@csrf_exempt
def update_rating_customer(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        id_rating = request.POST.get('id_rating')
        active_new = request.POST.get('action')
        if Rating_Customer.objects.filter(pk=id_rating).exists() == False:
            return HttpResponse('Đánh giá không tồn tại')
        rating = Rating_Customer.objects.get(pk=id_rating)
        rating.is_activity = active_new
        rating.save()
        return HttpResponse(1)
    return HttpResponse(503)

def payment_posts(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            list_payment = []
            payment_all = Purchase_Service.objects.filter(merchant_id_id=request.session.get('user')['id'])
            for item in payment_all:
                payment_item = []
                payment_item.append('<a href="/admin/payment_post_detail/'+ str(item.id) +'">'+ item.purchase_name +'</a>')
                payment_item.append('<a href="/admin/user/see/'+ str(item.merchant_id.id) +'">'+ item.merchant_id.name +'</a>')
                #payment_item.append('<a href="/admin/service/edit/'+ str(item.service_id.id) +'">'+ item.service_id.service_name +'</a>')
                payment_item.append(str(item.amount) + ' $')
                payment_item.append(str(item.success_at.replace(tzinfo=None)).split(' ')[0]+ ' ' +str(item.success_at.replace(tzinfo=None)).split(' ')[1].split('.')[0])
                if item.state == 1:
                    payment_item.append('<label class="label label-success">Thành công</label>')
                else:
                    payment_item.append('<label class="label label-danger">Thất bại</label>')
                list_payment.append(payment_item)
            return HttpResponse(json.dumps(list_payment, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
        return HttpResponse('No data')


def f_payment_post_detail(request, id_payment):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if Purchase_Service.objects.filter(pk=id_payment).exists() == False:
            return HttpResponse('Không tồn tại giao dịch!')
        payment =  Purchase_Service.objects.get(pk=id_payment).__dict__
        del payment['_state']
        merchant = Account.objects.filter(pk=payment['merchant_id_id']).values('name', 'email')[0]
        #del merchant['_state']
        service = Service.objects.get(pk=payment['service_id_id']).__dict__
        del service['_state']
        payment['merchant'] = merchant
        payment['service'] = service
        return HttpResponse(json.dumps(payment, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")




def payment_ads(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if request.GET.get('table') == 'true':
            list_payment = []
            payment_all = Purchase_Service_Ads.objects.all()
            for item in payment_all:
                payment_item = []
                payment_item.append('<a href="/admin/payment_ads_detail/'+ str(item.id) +'">'+ item.purchase_name +'</a>')
                payment_item.append('<a href="/admin/user/see/'+ str(item.merchant_id.id) +'">'+ item.merchant_id.name +'</a>')
                payment_item.append(str(item.amount) + ' VNĐ')
                payment_item.append(str(item.success_at.replace(tzinfo=None)).split(' ')[0]+ ' ' +str(item.success_at.replace(tzinfo=None)).split(' ')[1].split('.')[0])
                if item.state != 0:
                    payment_item.append('<label class="label label-success">Thanh toán thành công</label>')
                else:   
                    payment_item.append('<label class="label label-danger">Thanh toán thất bại</label>')
                list_payment.append(payment_item)
            return HttpResponse(json.dumps(list_payment, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")
        return HttpResponse('No data')
def f_payment_ads_detail(request, id_payment_ads):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'GET':
        if Purchase_Service_Ads.objects.filter(pk=id_payment_ads).exists() == False:
            return HttpResponse('Không tồn tại giao dịch!')
        payment =  Purchase_Service_Ads.objects.get(pk=id_payment_ads).__dict__
        del payment['_state']
        merchant = Account.objects.filter(pk=payment['merchant_id_id']).values('name', 'email')[0]
        #del merchant['_state']
        service = Service_Ads.objects.get(pk=payment['service_ads_id_id']).__dict__
        del service['_state']
        payment['merchant'] = merchant
        payment['service'] = service
        return HttpResponse(json.dumps(payment, sort_keys=False, indent=1, cls=DjangoJSONEncoder), content_type="application/json")


def send_email_notifile(email, body, content):

    mail = Mail(
        'smtp.gmail.com', 
        port='465', 
        username='dinhtai018@gmail.com', 
        password='wcyfglkfcshkxoaa',
        use_ssl=True,
        use_tls=False,
        debug_level=False
    )
    msg = Message(body)
    msg.fromaddr = ("Website C2C", "dinhtai018@gmail.com")
    msg.to = email
    msg.body = body
    msg.html = content
    msg.reply_to = 'no-reply@gmail.com'
    msg.charset = 'utf-8'
    msg.extra_headers = {}
    msg.mail_options = []
    msg.rcpt_options = []
    mail.send(msg)

## Ly Thanh - thong ke
@csrf_exempt
def getStatistical(request):
    if check_rule(request) == 0:
        return HttpResponse('Quyền truy cập bị từ chối')
    if request.method == 'POST':
        print(request.POST)
        typeget = int(request.POST.get('inputType'))
        date_start = datetime.strptime(request.POST.get('inputStart'), '%Y-%m-%d')
        date_end = datetime.strptime(request.POST.get('inputEnd'), '%Y-%m-%d')
        result = []
        if typeget == 1:
            _sum = 0
            for item in Purchase_Service.objects.filter(state=1,success_at__gte=date_start,success_at__lte=date_end):
                dict_service = dict()
                dict_service['label']=item.success_at.strftime("%d/%m/%Y")
                dict_service['value']=round(item.amount*22000,2)
                result.append(dict_service)
                _sum+=item.amount
            for item in Purchase_Service_Ads.objects.filter(state__gte=0,success_at__gte=date_start,success_at__lte=date_end):
                _sum+=item.amount
                dict_service = dict()
                dict_service['label']=item.success_at.strftime("%d/%m/%Y")
                dict_service['value']=item.amount
                result.append(dict_service)
            return HttpResponse(json.dumps({'result':result,'total':_sum}), content_type="application/json")
    return -1





