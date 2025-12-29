from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CategoryViewSet,
    ProductViewSet,
    CartViewSet,
    OrderViewSet,
    ImportProductsView,
    RegistrationView,
    LoginView,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("cart", CartViewSet, basename="cart")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("import-products/", ImportProductsView.as_view(), name="import_products"),
]
