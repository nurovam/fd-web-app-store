import json
import urllib.request
from django.conf import settings
from django.core.mail import send_mail


def _build_order_message(order):
    profile = getattr(order.user, 'profile', None)
    address = order.address
    lines = [
        f'Новый заказ #{order.id}',
        f'Клиент: {profile.full_name if profile and profile.full_name else order.user.username}',
        f'Телефон: {profile.phone if profile and profile.phone else "-"}',
        f'Клиника: {profile.clinic_name if profile and profile.clinic_name else "-"}',
        f'Адрес: {address.line1 if address else "-"}',
        f'Сумма: {order.total} c.',
        'Позиции:'
    ]
    for item in order.items.select_related('product', 'variant'):
        variant_label = ''
        if getattr(item, 'variant', None):
            variant = item.variant
            parts = []
            if variant.name:
                parts.append(f'Вариант: {variant.name}')
            color = (variant.attributes or {}).get('color')
            if color:
                parts.append(f'Цвет: {color}')
            if parts:
                variant_label = f" ({', '.join(parts)})"
        lines.append(f'- {item.product.name}{variant_label} x{item.quantity} ({item.price} c.)')
    return '\n'.join(lines)


def _send_telegram_message(message, chat_ids=None):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False
    targets = chat_ids or settings.TELEGRAM_ADMIN_CHAT_IDS or []
    if not targets and settings.TELEGRAM_CHAT_ID:
        targets = [settings.TELEGRAM_CHAT_ID]
    if not targets:
        return False
    for chat_id in targets:
        payload = {
            'chat_id': chat_id,
            'text': message,
        }
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/sendMessage',
            data=data,
            headers={'Content-Type': 'application/json'},
        )
        urllib.request.urlopen(request, timeout=5)
    return True


def notify_order_created(order):
    message = _build_order_message(order)
    if settings.ORDER_NOTIFICATION_EMAIL:
        try:
            send_mail(
                subject=f'Заказ #{order.id} оформлен',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ORDER_NOTIFICATION_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass

    try:
        _send_telegram_message(message)
    except Exception:
        pass


def notify_consultation_request(name, phone, message, page_url=None, request_id=None):
    lines = [
        'Запрос консультации',
        f'ID: {request_id}' if request_id else None,
        f'Имя: {name}',
        f'Телефон: {phone}',
    ]
    lines = [line for line in lines if line]
    if page_url:
        lines.append(f'Страница: {page_url}')
    if message:
        lines.append(f'Комментарий: {message}')
    payload = '\n'.join(lines)
    return _send_telegram_message(payload)
