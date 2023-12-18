from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from ecartapp.models import product,Cart,Order
from django.db.models import Q
import random
import razorpay
from django.core.mail import send_mail

# Create your views here.
def home(request):
    userid=request.user.id
    #print("id of logged in user :",userid)
    #print("Result:",request.user.is_authenticated)
    context={}
    p=product.objects.filter(is_active=True)
    context['products']=p
    print(p)
    return render(request,"index.html",context)

def pdetails(request,pid):
    context={}
    p=product.objects.filter(id=pid)
    context['products']=p
    print(p)
    return render(request,"pdetails.html",context)

def viewcart(request):
    c=Cart.objects.filter(uid=request.user.id)
    print(c)
    #print(c[0].pid)
    #print(c[0].uid)
    #print(c[0].pid.name)
    context={}
    context['data']=c

    s=0
    for x in c:
        print(x)
        print(x.pid.price)
        s=s+x.pid.price * x.qty
    print(s)
    context['total']=s
    np=len(c)
    context['items']=np
    return render(request,"viewcart.html",context)

def register(request):
    if request.method=="POST":
        uname=request.POST['uname']
        upass=request.POST['upass']
        ucpass=request.POST['ucpass']
        #print(uname)
        context={}
        if uname=="" or upass=="" or ucpass=="":
            context['errmsg']="Feilds cannot be empty"
            return render(request,"register.html",context)
        elif upass!=ucpass:
            context['errmsg']="Password did not match"
            return render(request,"register.html",context)
        else:
            try:
                u=User.objects.create(password=upass,username=uname,email=uname)
                u.set_password(upass)
                u.save()
                context['success']="User Registered Successfully"
                return render(request,"register.html",context)
                #return HttpResponse("Data Fetched")
            except Exception:
                context['errmsg']="Username already exists! Try Login."
                return render(request,"register.html",context)
    else:
        return render(request,"register.html")

def ulogin(request):
    if request.method=="POST":
        uname=request.POST['uname']
        upass=request.POST['upass']
        context={}
        if uname=="" or upass=="":
            context['errmsg']="Feilds cannot be empty"
            return render(request,"login.html",context)
            #print(uname)
            #print(upass)
            #return HttpResponse("Data Fetched")
        else:
            u=authenticate(username=uname,password=upass)
            #print(u)
            #print(u.username)
            #print(u.password)
            #print(u.is_superuser)
            if u is not None:
                login(request,u)
                return redirect('/home')
            else:
                context['errmsg']="Invalid Username/Password"
                return render(request,"login.html",context)        
    else:
        return render(request,"login.html")

def ulogout(request):
    logout(request)
    return redirect('/home')

def catfilter(request,cv):
    q1=Q(is_active=True)
    q2=Q(cat=cv)
    p=product.objects.filter(q1 & q2)
    print(p)
    context={}
    context['products']=p
    return render(request,"index.html",context)

def sort(request,sv):
    if sv=='0':
        col='price'
    else:
        col='-price'
    p=product.objects.filter(is_active=True).order_by(col)
    context={}
    context['products']=p
    return render(request,"index.html",context)

def range(request):
    min=request.GET['min']
    max=request.GET['max']
    q1=Q(price__gte=min)
    q2=Q(price__lte=max)
    q3=Q(is_active=True)
    p=product.objects.filter(q1 & q2 & q3) 
    context={}
    context['products']=p
    return render(request,"index.html",context)

def addtocart(request,pid):
    if request.user.is_authenticated:
        userid=request.user.id
        u=User.objects.filter(id=userid)
        print(u)
        p=product.objects.filter(id=pid)
        print(p)
        q1=Q(uid=u[0])
        q2=Q(pid=p[0])
        c=Cart.objects.filter(q1 & q2)
        print(c)
        context={}
        n=len(c)
        if n==1:
            context['errmsg']="Product already exists in Cart"
            context['products']=p
            return render(request,'pdetails.html',context)
        else:
            c=Cart.objects.create(uid=u[0],pid=p[0])
            c.save()
            context['success']="Product Added to Cart!"
            context['products']=p
            return render(request,'pdetails.html',context)
    else:
        return redirect('/login')  

def remove(request,cid):
    c=Cart.objects.filter(id=cid)
    c.delete()
    return redirect('/viewcart')

def updateqty(request,qv,cid):
    c=Cart.objects.filter(id=cid)
    print(c[0])
    print(c[0].qty)
    if qv=='1':
        t=c[0].qty+1
        c.update(qty=t)
    else:
        t=c[0].qty-1
        c.update(qty=t)

    return redirect('/viewcart')

def placeorder(request):
    userid=request.user.id
    c=Cart.objects.filter(uid=userid)
    oid=random.randrange(1000,9999)
    print(oid)
    for x in c:
        o=Order.objects.create(order_id=oid,uid=x.uid,pid=x.pid,qty=x.qty)
        o.save()
        x.delete()
    orders=Order.objects.filter(uid=request.user.id)
    context={}
    context['data']=orders
    s=0
    for x in orders:
        print(x)
        print(x.pid.price)
        s=s+x.pid.price * x.qty
    print(s)
    context['total']=s
    np=len(orders)
    context['items']=np
    return render(request,'placeorder.html',context)


def makepayment(request):
    orders=Order.objects.filter(uid=request.user.id)
    s=0
    np=len(orders)
    for x in orders:
        s=s+x.pid.price * x.qty
        oid=x.order_id
    
    client = razorpay.Client(auth=("rzp_test_YvjZinDbG3pKzW", "3ahukKWs5YofrX6HW2Y8cCi9"))

    data = { "amount": s*100, "currency": "INR", "receipt": oid }
    payment = client.order.create(data=data)
    context={}
    context['data']=payment
    #return HttpResponse("In Payment Page")
    return render(request,'pay.html',context)

def sendusermail(request):
    send_mail(
    "Ecart-Order Placed Successfully",
    "Order Completed!! Thanks for ordering",
    "tejashripshinde002@gmail.com",
    ["tejashriprakashshinde25702@gmail.com"],
    fail_silently=False,
    )
    return HttpResponse("Email Sent!!")