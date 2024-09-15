from django.contrib import admin
from django.urls import path, include
from backend.apps import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
   openapi.Info(
      title="Tenders API",
      default_version='v1.1',
      description="API for better user experience developed specifically for Tenders-app",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="ikworkmail@yandex.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path(r'api/ping', views.ping, name='ping'),

    path(r'api/tenders', views.get_tenders, name='tenders-list'),
    path(r'api/tenders/my', views.get_user_tenders, name='my-tenders'),
    path(r'api/tenders/new', views.create_tender, name='create-tender'),
    path(r'api/tenders/<int:tender_id>/status', views.tender_status, name='upd-tender-status'),
    path(r'api/tenders/<int:tender_id>/edit', views.edit_tender, name='edit-tender'),
    path(r'api/tenders/<int:tender_id>/rollback/<int:version>/', views.rollback_tender_version, name='rollback-tender'),

    path(r'api/bids/<int:tender_id>/list', views.get_bids_for_tender, name='bids-list'),
    path(r'api/bids/my', views.get_user_bids, name='my-bids'),
    path(r'api/bids/new', views.create_bid, name='create-bid'),
    path(r'api/bids/<int:bid_id>/status', views.bid_status, name='upd-bid-status'),
    path(r'api/bids/<int:bid_id>/edit', views.edit_bid, name='edit-bid'),
    path(r'api/bids/submit_decision', views.submit_decision, name='submit-decision'),
    path(r'api/bids/<int:bid_id>/rollback/<int:version>/', views.rollback_bid_version, name='rollback-bid'),

    path(r'api/bids/<int:tender_id>/reviews', views.get_reviews, name='get-reviews'),
    path(r'api/bids/<int:bid_id>/feedback', views.create_review, name='leave-feedback'),
]