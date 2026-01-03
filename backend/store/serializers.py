import re
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductVariant,
    Profile,
)

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=160, write_only=True)
    phone = serializers.CharField(max_length=40, write_only=True)
    clinic_name = serializers.CharField(max_length=160, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password_confirm', 'full_name', 'phone', 'clinic_name')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate_full_name(self, value):
        cleaned = value.strip()
        if len(cleaned.split()) < 2:
            raise serializers.ValidationError('Укажите фамилию и имя.')
        sanitized = cleaned.replace(' ', '').replace('-', '').replace("'", '')
        if not sanitized.isalpha():
            raise serializers.ValidationError('ФИО может содержать только буквы, пробелы и дефисы.')
        return cleaned

    def validate_email(self, value):
        cleaned = value.strip().lower()
        max_username_length = User._meta.get_field('username').max_length
        if len(cleaned) > max_username_length:
            raise serializers.ValidationError('Email слишком длинный.')
        if User.objects.filter(email__iexact=cleaned).exists() or User.objects.filter(
            username__iexact=cleaned
        ).exists():
            raise serializers.ValidationError('Пользователь с такой почтой уже существует.')
        return cleaned

    def validate_phone(self, value):
        cleaned = value.strip()
        if not re.match(r'^[0-9+()\s.-]+$', cleaned):
            raise serializers.ValidationError('Укажите номер телефона в допустимом формате.')
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) < 10 or len(digits) > 15:
            raise serializers.ValidationError('Номер телефона должен содержать от 10 до 15 цифр.')
        if cleaned.startswith('+'):
            return f'+{digits}'
        return digits

    def validate_clinic_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Название организации слишком короткое.')
        return cleaned

    def validate_password(self, value):
        missing_parts = []
        if not re.search(r'[a-z]', value):
            missing_parts.append('строчную букву')
        if not re.search(r'[A-Z]', value):
            missing_parts.append('заглавную букву')
        if not re.search(r'\d', value):
            missing_parts.append('цифру')
        if not re.search(r'[^A-Za-z0-9]', value):
            missing_parts.append('спецсимвол')
        messages = []
        if missing_parts:
            messages.append(f"Пароль должен содержать: {', '.join(missing_parts)}.")
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            messages.extend(exc.messages)
        if messages:
            raise serializers.ValidationError(messages)
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.full_name = validated_data['full_name']
        profile.phone = validated_data['phone']
        profile.clinic_name = validated_data['clinic_name']
        profile.save(update_fields=['full_name', 'phone', 'clinic_name'])
        return user


class ConsultationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    phone = serializers.CharField(max_length=40)
    message = serializers.CharField(max_length=800, required=False, allow_blank=True)
    page_url = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Укажите имя.')
        return cleaned

    def validate_phone(self, value):
        cleaned = value.strip()
        if not re.match(r'^[0-9+()\s.-]+$', cleaned):
            raise serializers.ValidationError('Укажите номер телефона в допустимом формате.')
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) < 10 or len(digits) > 15:
            raise serializers.ValidationError('Номер телефона должен содержать от 10 до 15 цифр.')
        if cleaned.startswith('+'):
            return f'+{digits}'
        return digits


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    image_url = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'category',
            'category_id',
            'name',
            'slug',
            'description',
            'price',
            'is_available',
            'stock_quantity',
            'image',
            'image_url',
            'variants',
            'created_at',
        )

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ''

    def get_variants(self, obj):
        variants = obj.variants.all().order_by('id')
        return ProductVariantSerializer(variants, many=True).data


class ProductVariantSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = ProductVariant
        fields = ('id', 'name', 'attributes', 'label', 'price', 'stock_quantity', 'is_available')

    def get_label(self, obj):
        if obj.name:
            return obj.name
        if obj.attributes:
            return ', '.join(f'{key}: {value}' for key, value in obj.attributes.items())
        return f'Variant {obj.id}'

    def validate_attributes(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            cleaned = dict(value)
            cleaned.pop('size', None)
            return cleaned
        return value


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('full_name', 'phone', 'clinic_name')


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'label',
            'line1',
            'line2',
            'city',
            'region',
            'postal_code',
            'country',
            'is_default',
        )


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'variant', 'variant_id', 'quantity')

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        return value

    def validate(self, attrs):
        product = attrs.get('product') or getattr(self.instance, 'product', None)
        variant = attrs.get('variant') if 'variant' in attrs else getattr(self.instance, 'variant', None)
        if product and product.variants.exists():
            if not variant:
                raise serializers.ValidationError({'variant_id': 'Variant is required.'})
            if variant.product_id != product.id:
                raise serializers.ValidationError({'variant_id': 'Variant does not belong to product.'})
        if variant and product and variant.product_id != product.id:
            raise serializers.ValidationError({'variant_id': 'Variant does not belong to product.'})
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'items', 'updated_at')


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'variant', 'quantity', 'price')


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('provider', 'status', 'reference', 'amount', 'created_at')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    address_detail = AddressSerializer(source='address', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'total', 'created_at', 'address', 'address_detail', 'items', 'payment')
