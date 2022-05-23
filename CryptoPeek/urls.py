from django.urls import path
from . import views
app_name = 'CryptoPeek'
urlpatterns = [
    path('',views.home,name="home"),
    path('home/',views.home,name="home"),
    path('favourite/',views.favourite,name="favourite"),
    path('favourite/login/',views.account,name="account"),
    path('login/',views.account,name="account"),
    path('delete/<str:crypto_id>/',views.delete,name="delete"),
    path('register/',views.register,name="register"),
    path('currencies/', views.index, name='currencies'),
    path('<str:crypto_id>/', views.detail, name='detail')
]