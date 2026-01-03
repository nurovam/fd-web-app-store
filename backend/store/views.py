from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    ConsultationRequest,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductVariant,
    Profile,
)
from .notifications import notify_consultation_request, notify_order_created
from .permissions import IsStaffOrManager, IsStaffOrReadOnly
from .filters import ProductFilter
from .pagination import OptionalPageNumberPagination
from .pricelist import build_price_list_pdf
from .serializers import (
    AddressSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    OrderSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    ProfileSerializer,
    ConsultationSerializer,
    RegisterSerializer,
    UserSummarySerializer,
)

def _get_cart_with_items(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return Cart.objects.filter(id=cart.id).prefetch_related(
        Prefetch(
            'items',
            queryset=CartItem.objects.select_related('product', 'variant', 'product__category')
        )
    ).first()


def _get_cache_key(prefix, request):
    host = request.get_host()
    return f'{prefix}:{host}:{request.get_full_path()}'


def _get_cookie_domain():
    return settings.JWT_AUTH_COOKIE_DOMAIN or None


def _set_auth_cookie(response, name, value, max_age, path):
    if not value:
        return
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        domain=_get_cookie_domain(),
        path=path,
    )


def _set_auth_cookies(response, access, refresh=None):
    access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    _set_auth_cookie(
        response,
        settings.JWT_AUTH_COOKIE,
        access,
        int(access_lifetime.total_seconds()),
        settings.JWT_AUTH_COOKIE_PATH,
    )
    if refresh:
        _set_auth_cookie(
            response,
            settings.JWT_AUTH_REFRESH_COOKIE,
            refresh,
            int(refresh_lifetime.total_seconds()),
            settings.JWT_AUTH_REFRESH_COOKIE_PATH,
        )


def _clear_auth_cookies(response):
    response.delete_cookie(
        settings.JWT_AUTH_COOKIE,
        domain=_get_cookie_domain(),
        path=settings.JWT_AUTH_COOKIE_PATH,
    )
    response.delete_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        domain=_get_cookie_domain(),
        path=settings.JWT_AUTH_REFRESH_COOKIE_PATH,
    )


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        if 'refresh' not in attrs:
            attrs['refresh'] = self.context['request'].COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        return super().validate(attrs)


@method_decorator(csrf_protect, name='dispatch')
class AuthTokenView(TokenObtainPairView):
    throttle_scope = 'auth'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access = response.data.get('access')
            refresh = response.data.get('refresh')
            _set_auth_cookies(response, access, refresh)
            response.data = {'detail': 'ok'}
        return response


@method_decorator(csrf_protect, name='dispatch')
class AuthTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access = response.data.get('access')
            refresh = response.data.get('refresh')
            _set_auth_cookies(response, access, refresh)
            response.data = {'detail': 'ok'}
        return response


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        response = Response({'detail': 'ok'})
        _clear_auth_cookies(response)
        return response


class CsrfView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'detail': 'ok'})


@method_decorator(csrf_protect, name='dispatch')
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth'
    throttle_classes = [ScopedRateThrottle]


@method_decorator(csrf_protect, name='dispatch')
class ConsultationView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'contact'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = ConsultationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        page_url = data.get('page_url') or request.META.get('HTTP_REFERER', '')
        consultation = ConsultationRequest.objects.create(
            name=data['name'],
            phone=data['phone'],
            message=data.get('message', ''),
            page_url=page_url,
        )
        try:
            delivered = notify_consultation_request(
                data['name'],
                data['phone'],
                data.get('message', ''),
                page_url=page_url,
                request_id=consultation.id,
            )
        except Exception:
            return Response({'detail': 'Не удалось отправить запрос.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not delivered:
            return Response({'detail': 'Telegram не настроен.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'detail': 'ok'}, status=status.HTTP_201_CREATED)


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().list(request, *args, **kwargs)
        cache_key = _get_cache_key('categories', request)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, settings.API_CACHE_TTL)
        return response


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related('variants')
        .all()
        .order_by('-created_at')
    )
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = OptionalPageNumberPagination
    filterset_class = ProductFilter
    ordering_fields = ['price', 'created_at', 'stock_quantity']
    search_fields = ['name', 'description', 'category__name']

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().list(request, *args, **kwargs)
        cache_key = _get_cache_key('products', request)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, settings.API_CACHE_TTL)
        return response

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PriceListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cache_key = _get_cache_key('pricelist', request)
        cached = cache.get(cache_key)
        if cached:
            return self._build_response(cached)
        products = (
            Product.objects.select_related('category')
            .prefetch_related('variants')
            .all()
            .order_by('category__name', 'name')
        )
        pdf_bytes = build_price_list_pdf(products)
        cache.set(cache_key, pdf_bytes, settings.PRICE_LIST_CACHE_TTL)
        return self._build_response(pdf_bytes)

    def _build_response(self, pdf_bytes):
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pricelist.pdf"'
        return response


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category').prefetch_related('variants').all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrManager]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            users_qs = (
                OrderItem.objects.filter(product=instance)
                .select_related('order__user')
                .values_list('order__user__username', flat=True)
                .distinct()
            )
            users = list(users_qs[:5])
            total_users = users_qs.count()
            users_label = ', '.join(users) if users else 'неизвестно'
            extra = f' Пользователи: {users_label}.' if users else ''
            if total_users > len(users):
                extra = f' Пользователи: {users_label} и еще {total_users - len(users)}.' if users else extra
            return Response(
                {'detail': f'Нельзя удалить товар с заказами.{extra}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductVariantListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs['product_id']).order_by('id')

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        serializer.save(product=product)


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsStaffOrManager]
    queryset = ProductVariant.objects.select_related('product')


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSummarySerializer(request.user).data)


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-is_default', 'label')

    def perform_create(self, serializer):
        if serializer.validated_data.get('is_default', False):
            Address.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
        serializer.save(user=self.request.user)


class AddressDetailView(generics.UpdateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.validated_data.get('is_default', False):
            Address.objects.filter(user=self.request.user, is_default=True).exclude(
                id=self.get_object().id
            ).update(is_default=False)
        serializer.save()


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = _get_cart_with_items(request.user)
        return Response(CartSerializer(cart, context={'request': request}).data)

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        variant = serializer.validated_data.get('variant')
        quantity = serializer.validated_data.get('quantity', 1)
        if product.variants.exists() and not variant:
            return Response({'detail': 'Variant is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if variant and variant.product_id != product.id:
            return Response({'detail': 'Variant does not belong to product.'}, status=status.HTTP_400_BAD_REQUEST)
        if not variant and not product.is_available:
            return Response({'detail': 'Product is not available.'}, status=status.HTTP_400_BAD_REQUEST)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
        new_quantity = item.quantity + quantity if not created else quantity
        if variant:
            if not variant.is_available or variant.stock_quantity < new_quantity:
                return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
        elif product.stock_quantity < new_quantity:
            return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = new_quantity
        item.save()
        cart = _get_cart_with_items(request.user)
        return Response(CartSerializer(cart, context={'request': request}).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartItemSerializer(item, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data.get('quantity', item.quantity)
        if new_quantity < 1:
            return Response({'detail': 'Quantity must be at least 1.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_quantity > item.quantity:
            if item.variant:
                if not item.variant.is_available or item.variant.stock_quantity < new_quantity:
                    return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if not item.product.is_available:
                    return Response({'detail': 'Product is not available.'}, status=status.HTTP_400_BAD_REQUEST)
                if item.product.stock_quantity < new_quantity:
                    return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        cart = _get_cart_with_items(request.user)
        return Response(CartSerializer(cart, context={'request': request}).data)

    def delete(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.filter(id=item_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .select_related('address', 'payment')
            .prefetch_related('items__product__category', 'items__variant')
            .order_by('-created_at')
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request, view=self)
        if page is not None:
            serializer = OrderSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        return Response(OrderSerializer(orders, many=True, context={'request': request}).data)

    @transaction.atomic
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = list(cart.items.select_related('product', 'variant'))
        if not cart_items:
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)
        address_id = request.data.get('address_id')
        address = None
        if address_id:
            address = Address.objects.filter(user=request.user, id=address_id).first()
        if not address:
            address = Address.objects.filter(user=request.user, is_default=True).first()
        product_ids = [item.product_id for item in cart_items if item.variant_id is None]
        variant_ids = [item.variant_id for item in cart_items if item.variant_id]
        products = Product.objects.select_for_update().filter(id__in=product_ids).in_bulk()
        variants = (
            ProductVariant.objects.select_for_update()
            .select_related('product')
            .filter(id__in=variant_ids)
            .in_bulk()
        )
        total = Decimal('0')
        for item in cart_items:
            if item.variant_id:
                variant = variants.get(item.variant_id)
                if not variant or not variant.is_available:
                    return Response({'detail': 'Product is not available.'}, status=status.HTTP_400_BAD_REQUEST)
                if variant.stock_quantity < item.quantity:
                    return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                product = products.get(item.product_id)
                if not product or not product.is_available:
                    return Response({'detail': 'Product is not available.'}, status=status.HTTP_400_BAD_REQUEST)
                if product.stock_quantity < item.quantity:
                    return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.create(user=request.user, address=address)
        for item in cart_items:
            variant = variants.get(item.variant_id) if item.variant_id else None
            product = variant.product if variant else products.get(item.product_id)
            item_price = variant.price if variant and variant.price is not None else product.price
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=item.quantity,
                price=item_price,
            )
            if variant:
                variant.stock_quantity -= item.quantity
                if variant.stock_quantity < 0:
                    variant.stock_quantity = 0
                variant.save(update_fields=['stock_quantity'])
            else:
                product.stock_quantity -= item.quantity
                if product.stock_quantity <= 0:
                    product.stock_quantity = 0
                    product.is_available = False
                product.save(update_fields=['stock_quantity', 'is_available'])
            total += item_price * item.quantity
        order.total = total
        order.save()
        Payment.objects.create(order=order, amount=total)
        cart.items.all().delete()
        transaction.on_commit(lambda: notify_order_created(order))
        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)


class OrderPaymentView(APIView):
    permission_classes = [IsStaffOrManager]

    def post(self, request, order_id):
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        payment = getattr(order, 'payment', None)
        if not payment:
            payment = Payment.objects.create(order=order, amount=order.total)
        payment.status = Payment.STATUS_PAID
        payment.reference = request.data.get('reference', payment.reference)
        payment.save()
        order.status = Order.STATUS_PAID
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrdersAdminView(APIView):
    permission_classes = [IsStaffOrManager]
    pagination_class = OptionalPageNumberPagination

    def get(self, request):
        orders = (
            Order.objects.select_related('user', 'address', 'payment')
            .prefetch_related('items__product__category', 'items__variant')
            .order_by('-created_at')
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request, view=self)
        if page is not None:
            serializer = OrderSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        return Response(OrderSerializer(orders, many=True, context={'request': request}).data)


class OrderStatusView(APIView):
    permission_classes = [IsStaffOrManager]

    def post(self, request, order_id):
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        status_value = request.data.get('status')
        valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
        if status_value not in valid_statuses:
            return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = status_value
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        order = Order.objects.select_for_update().filter(id=order_id, user=request.user).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        order = (
            Order.objects.filter(id=order.id)
            .select_related('payment')
            .prefetch_related('items__product')
            .first()
        )
        if order.status != Order.STATUS_PENDING:
            return Response({'detail': 'Order cannot be canceled.'}, status=status.HTTP_400_BAD_REQUEST)
        if getattr(order, 'payment', None) and order.payment.status == Payment.STATUS_PAID:
            return Response({'detail': 'Paid order cannot be canceled.'}, status=status.HTTP_400_BAD_REQUEST)
        items = list(order.items.select_related('variant'))
        variant_ids = [item.variant_id for item in items if item.variant_id]
        product_ids = [item.product_id for item in items if not item.variant_id]
        variants = ProductVariant.objects.select_for_update().filter(id__in=variant_ids).in_bulk()
        products = Product.objects.select_for_update().filter(id__in=product_ids).in_bulk()
        for item in items:
            if item.variant_id:
                variant = variants.get(item.variant_id)
                if not variant:
                    continue
                variant.stock_quantity += item.quantity
                variant.save(update_fields=['stock_quantity'])
            else:
                product = products.get(item.product_id)
                if not product:
                    continue
                product.stock_quantity += item.quantity
                if product.stock_quantity > 0:
                    product.is_available = True
                product.save(update_fields=['stock_quantity', 'is_available'])
        order.status = Order.STATUS_CANCELED
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, order_id):
        order = Order.objects.filter(id=order_id, user=request.user).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status != Order.STATUS_CANCELED:
            return Response({'detail': 'Only canceled orders can be deleted.'}, status=status.HTTP_400_BAD_REQUEST)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthView(APIView):
    def get_permissions(self):
        if settings.HEALTHCHECK_PUBLIC:
            return [permissions.AllowAny()]
        return [IsStaffOrManager()]

    def get(self, request):
        return Response({'status': 'ok'})
