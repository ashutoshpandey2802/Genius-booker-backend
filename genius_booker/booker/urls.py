from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterUserView, LoginUserView, LogoutUserView, StoreViewSet, StaffViewSet,AppointmentViewSet

router = DefaultRouter()
router.register(r'stores', StoreViewSet)
router.register(r'staff', StaffViewSet)
router.register(r'appointments', AppointmentViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('', include(router.urls)),  
]
