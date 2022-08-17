from django.urls import path
from . import views


urlpatterns = [
    path('', views.index ),
    path('recent', views.GetRecent.as_view() ),
    path('media/<int:id>/', views.GetDetail.as_view() ),
    path('submit', views.SubmitUrl.as_view() ),
    path('submit/<id>', views.SubmitUrl.as_view() )
]