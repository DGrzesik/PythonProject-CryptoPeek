from django.urls import path
from . import views
app_name = 'CryptoPeek'
urlpatterns = [
    path('',views.home,name="home"),
    path('cryptopeek/home/',views.home,name="home"),
    path('cryptopeek/favourite/',views.favourite,name="favourite"),
    path('cryptopeek/favourite/login/',views.account,name="account"),
    path('cryptopeek/login/',views.account,name="account"),
    path('cryptopeek/delete/<str:crypto_id>/',views.delete,name="delete"),
    path('cryptopeek/register/',views.register,name="register"),
    path('cryptopeek/currencies/', views.index, name='currencies'),
    path('cryptopeek/<str:crypto_id>/', views.detail, name='detail')
]