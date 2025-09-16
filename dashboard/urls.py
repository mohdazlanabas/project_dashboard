from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from .views import LorryViewSet, TransactionViewSet, AggregatedDataAPIView

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('aggregated-table/', views.aggregated_table, name='aggregated_table'),
    path('chat/', views.dashboard_chat, name='dashboard_chat'),
]

router = DefaultRouter()
router.register(r'api/lorries', LorryViewSet, basename='lorry')
router.register(r'api/transactions', TransactionViewSet, basename='transaction')

urlpatterns += router.urls
urlpatterns += [
    path('api/aggregated/', AggregatedDataAPIView.as_view(), name='aggregated_api'),
]