from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'design-projects', views.DesignProjectViewSet, basename='design-project')
router.register(r'groups', views.GroupViewSet, basename='group')
router.register(r'prototypes', views.PrototypeViewSet, basename='prototype')
router.register(r'variants', views.PrototypeVariantViewSet, basename='variant')
router.register(r'versions', views.PrototypeVersionViewSet, basename='version')

urlpatterns = [
    path('', include(router.urls)),
    path('design-projects/<uuid:project_id>/prototypes/', views.design_project_prototypes, name='design-project-prototypes'),
    path('groups/<uuid:group_id>/prototypes/', views.group_prototypes, name='group-prototypes'),
    path('generate-prototype/', views.generate_prototype, name='generate-prototype'),
] 