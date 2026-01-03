import html
import json
import ssl
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, time as dt_time, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.utils import timezone

from store.models import ConsultationRequest, Order, Product
from store.pricelist import build_price_list_pdf
from store.reporting import build_orders_report_pdf


STATUS_LABELS = {
    Order.STATUS_PENDING: 'Ожидает',
    Order.STATUS_PAID: 'Оплачен',
    Order.STATUS_SHIPPED: 'В пути',
    Order.STATUS_RECEIVED: 'Получен',
    Order.STATUS_CANCELED: 'Отменен',
}

STATUS_BUTTONS = {
    Order.STATUS_PAID: '✅ Оплачен',
    Order.STATUS_SHIPPED: '🚚 В пути',
    Order.STATUS_RECEIVED: '📦 Получен',
    Order.STATUS_CANCELED: '❌ Отменить',
}

STATUS_TRANSITIONS = {
    Order.STATUS_PENDING: [Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_CANCELED],
    Order.STATUS_PAID: [Order.STATUS_SHIPPED, Order.STATUS_RECEIVED, Order.STATUS_CANCELED],
    Order.STATUS_SHIPPED: [Order.STATUS_RECEIVED, Order.STATUS_CANCELED],
    Order.STATUS_RECEIVED: [],
    Order.STATUS_CANCELED: [],
}

ORDER_PAGE_SIZE = 5
CONSULTATION_PAGE_SIZE = 5


class TelegramBotClient:
    def __init__(self, token):
        self.base_url = f'https://api.telegram.org/bot{token}/'

    def request(self, method, payload=None):
        data = json.dumps(payload or {}).encode('utf-8')
        request = urllib.request.Request(
            f'{self.base_url}{method}',
            data=data,
            headers={'Content-Type': 'application/json'},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, ssl.SSLError, TimeoutError):
            return None

    def get_updates(self, offset=None, timeout=30):
        payload = {'timeout': timeout}
        if offset is not None:
            payload['offset'] = offset
        return self.request('getUpdates', payload) or {'result': []}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode='HTML', disable_preview=True):
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_preview,
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.request('sendMessage', payload)

    def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode='HTML'):
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.request('editMessageText', payload)

    def answer_callback_query(self, callback_query_id, text=None):
        payload = {'callback_query_id': callback_query_id}
        if text:
            payload['text'] = text
        return self.request('answerCallbackQuery', payload)

    def send_document(self, chat_id, filename, data_bytes, caption=None):
        boundary = f'----fd{uuid.uuid4().hex}'
        body = []

        def _add_field(name, value):
            body.append(f'--{boundary}\r\n'.encode())
            body.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            body.append(str(value).encode())
            body.append(b'\r\n')

        def _add_file(name, file_name, content_type, data):
            body.append(f'--{boundary}\r\n'.encode())
            body.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{file_name}"\r\n'.encode()
            )
            body.append(f'Content-Type: {content_type}\r\n\r\n'.encode())
            body.append(data)
            body.append(b'\r\n')

        _add_field('chat_id', chat_id)
        if caption:
            _add_field('caption', caption)
        _add_file('document', filename, 'application/pdf', data_bytes)
        body.append(f'--{boundary}--\r\n'.encode())

        request = urllib.request.Request(
            f'{self.base_url}sendDocument',
            data=b''.join(body),
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, ssl.SSLError, TimeoutError):
            return None

    def delete_message(self, chat_id, message_id):
        payload = {'chat_id': chat_id, 'message_id': message_id}
        return self.request('deleteMessage', payload)


class Command(BaseCommand):
    help = 'Run Telegram bot for managing orders and consultations.'

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stdout.write(self.style.ERROR('TELEGRAM_BOT_TOKEN is not set.'))
            return

        allowed_chat_ids = set(settings.TELEGRAM_ADMIN_CHAT_IDS or [])
        if not allowed_chat_ids and settings.TELEGRAM_CHAT_ID:
            allowed_chat_ids = {int(settings.TELEGRAM_CHAT_ID)}
        if not allowed_chat_ids:
            self.stdout.write(self.style.ERROR('TELEGRAM_ADMIN_CHAT_IDS is not set.'))
            return

        bot = TelegramBotClient(token)
        offset = None
        self.chat_states = {}
        self.stdout.write(self.style.SUCCESS('Telegram order bot started.'))

        while True:
            try:
                updates = bot.get_updates(offset=offset, timeout=30)
            except urllib.error.URLError:
                time.sleep(2)
                continue

            for update in updates.get('result', []):
                offset = update.get('update_id', 0) + 1
                if 'message' in update:
                    self._handle_message(bot, update['message'], allowed_chat_ids)
                elif 'callback_query' in update:
                    self._handle_callback(bot, update['callback_query'], allowed_chat_ids)

    def _handle_message(self, bot, message, allowed_chat_ids):
        chat_id = message.get('chat', {}).get('id')
        if chat_id not in allowed_chat_ids:
            return

        text = (message.get('text') or '').strip()
        text_lower = text.lower()
        state = self.chat_states.get(chat_id)

        if text_lower in {'/start', '/menu', 'меню'}:
            self._send_main_menu(bot, chat_id)
            return

        if text_lower in {'/cancel', 'отмена'}:
            self.chat_states.pop(chat_id, None)
            bot.send_message(chat_id, 'Действие отменено.')
            self._send_main_menu(bot, chat_id)
            return

        if state == 'awaiting_order_id':
            self.chat_states.pop(chat_id, None)
            if not text.isdigit():
                bot.send_message(chat_id, 'Введите только номер заказа, например 102.')
                return
            order = (
                Order.objects.filter(id=int(text))
                .select_related('user', 'address')
                .prefetch_related('items__product', 'items__variant')
                .first()
            )
            if not order:
                bot.send_message(chat_id, 'Заказ не найден.')
                return
            bot.send_message(chat_id, self._format_order(order), reply_markup=self._build_status_keyboard(order))
            return

        if isinstance(state, dict) and state.get('mode') == 'awaiting_report_period':
            period = self._parse_period(text)
            if not period:
                bot.send_message(chat_id, 'Формат периода: 01.09.2024-30.09.2024.')
                self.chat_states[chat_id] = {'mode': 'awaiting_report_period'}
                return
            self.chat_states.pop(chat_id, None)
            start_date, end_date = period
            label = f'Период: {start_date:%d.%m.%Y}–{end_date:%d.%m.%Y}'
            self._send_report(bot, chat_id, start_date=start_date, end_date=end_date, period_label=label)
            return

        if text_lower in {'заказы', 'активные заказы'}:
            self._send_orders_menu(bot, chat_id)
            return

        if text_lower in {'консультации'}:
            self._send_consultations_menu(bot, chat_id)
            return

        if text_lower in {'статистика'}:
            self._send_stats(bot, chat_id)
            return

        if text_lower in {'отчет', 'отчёт', 'скачать отчет', 'скачать отчёт'}:
            self._send_report_menu(bot, chat_id)
            return

        if text_lower in {'прайс-лист', 'прайс'}:
            self._send_pricelist(bot, chat_id)
            return

        bot.send_message(chat_id, 'Напишите "меню" или используйте кнопки ниже.')
        self._send_main_menu(bot, chat_id)

    def _handle_callback(self, bot, callback_query, allowed_chat_ids):
        message = callback_query.get('message') or {}
        chat_id = message.get('chat', {}).get('id')
        message_id = message.get('message_id')
        if chat_id not in allowed_chat_ids:
            bot.answer_callback_query(callback_query.get('id'), 'Нет доступа.')
            return

        data = callback_query.get('data') or ''
        if data.startswith('menu:'):
            section = data.split(':', 1)[1]
            if section == 'main':
                self._send_main_menu(bot, chat_id)
            elif section == 'orders':
                self._send_orders_menu(bot, chat_id)
            elif section == 'consultations':
                self._send_consultations_menu(bot, chat_id)
            elif section == 'stats':
                self._send_stats(bot, chat_id)
            elif section == 'help':
                self._send_help(bot, chat_id)
            elif section == 'report':
                self._send_report_menu(bot, chat_id)
            bot.answer_callback_query(callback_query.get('id'))
            self._safe_delete_message(bot, chat_id, message_id)
            return

        if data.startswith('orders:'):
            parts = data.split(':')
            action = parts[1] if len(parts) > 1 else ''
            page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            if action == 'active':
                self._send_orders_list(bot, chat_id, scope='active', page=page)
            elif action == 'today':
                self._send_orders_list(bot, chat_id, scope='today', page=page)
            elif action == 'search':
                self.chat_states[chat_id] = 'awaiting_order_id'
                bot.send_message(chat_id, 'Введите номер заказа.')
            bot.answer_callback_query(callback_query.get('id'))
            self._safe_delete_message(bot, chat_id, message_id)
            return

        if data.startswith('order:status:'):
            _, _, order_id, status_value = data.split(':', 3)
            order = (
                Order.objects.filter(id=order_id)
                .select_related('user', 'address')
                .prefetch_related('items__product', 'items__variant')
                .first()
            )
            if not order:
                bot.answer_callback_query(callback_query.get('id'), 'Заказ не найден.')
                return
            if order.status == Order.STATUS_CANCELED:
                bot.answer_callback_query(callback_query.get('id'), 'Заказ отменен.')
                return
            if status_value not in {choice[0] for choice in Order.STATUS_CHOICES}:
                bot.answer_callback_query(callback_query.get('id'), 'Неверный статус.')
                return

            order.status = status_value
            order.save(update_fields=['status'])
            new_text = self._format_order(order)
            reply_markup = self._build_status_keyboard(order)
            bot.edit_message_text(chat_id, message.get('message_id'), new_text, reply_markup=reply_markup)
            bot.answer_callback_query(callback_query.get('id'), 'Статус обновлен.')
            return

        if data.startswith('consultations:'):
            parts = data.split(':')
            action = parts[1] if len(parts) > 1 else ''
            page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            if action == 'new':
                self._send_consultations_list(bot, chat_id, scope='new', page=page)
            elif action == 'recent':
                self._send_consultations_list(bot, chat_id, scope='recent', page=page)
            bot.answer_callback_query(callback_query.get('id'))
            self._safe_delete_message(bot, chat_id, message_id)
            return

        if data.startswith('report:'):
            action = data.split(':', 1)[1]
            if action == 'all':
                self._send_report(bot, chat_id, period_label='За все время')
            elif action == 'last30':
                end_date = timezone.localdate()
                start_date = end_date - timedelta(days=30)
                label = f'Период: {start_date:%d.%m.%Y}–{end_date:%d.%m.%Y}'
                self._send_report(bot, chat_id, start_date=start_date, end_date=end_date, period_label=label)
            elif action == 'custom':
                self.chat_states[chat_id] = {'mode': 'awaiting_report_period'}
                bot.send_message(chat_id, 'Введите период: 01.09.2024-30.09.2024.')
            bot.answer_callback_query(callback_query.get('id'))
            self._safe_delete_message(bot, chat_id, message_id)
            return

        if data.startswith('consultation:done:'):
            request_id = data.split(':', 2)[2]
            consultation = ConsultationRequest.objects.filter(id=request_id).first()
            if not consultation:
                bot.answer_callback_query(callback_query.get('id'), 'Запрос не найден.')
                return
            if consultation.status == ConsultationRequest.STATUS_DONE:
                bot.answer_callback_query(callback_query.get('id'), 'Уже закрыт.')
                return
            consultation.status = ConsultationRequest.STATUS_DONE
            consultation.handled_at = timezone.now()
            consultation.save(update_fields=['status', 'handled_at'])
            new_text = self._format_consultation(consultation)
            bot.edit_message_text(chat_id, message.get('message_id'), new_text)
            bot.answer_callback_query(callback_query.get('id'), 'Запрос закрыт.')
            return

        bot.answer_callback_query(callback_query.get('id'))

    def _safe_delete_message(self, bot, chat_id, message_id):
        if not message_id:
            return
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

    def _send_main_menu(self, bot, chat_id):
        keyboard = {
            'inline_keyboard': [
                [{'text': '🧾 Заказы', 'callback_data': 'menu:orders'}],
                [{'text': '🧑‍⚕️ Консультации', 'callback_data': 'menu:consultations'}],
                [
                    {'text': '📊 Статистика', 'callback_data': 'menu:stats'},
                    {'text': '📄 Скачать отчет', 'callback_data': 'menu:report'},
                ],
                [{'text': 'ℹ️ Помощь', 'callback_data': 'menu:help'}],
            ]
        }
        bot.send_message(chat_id, 'Выберите действие:', reply_markup=keyboard)

    def _send_orders_menu(self, bot, chat_id):
        keyboard = {
            'inline_keyboard': [
                [{'text': 'Активные заказы', 'callback_data': 'orders:active:1'}],
                [{'text': 'За сегодня', 'callback_data': 'orders:today:1'}],
                [{'text': 'Найти по номеру', 'callback_data': 'orders:search'}],
                [{'text': '⬅️ Главное меню', 'callback_data': 'menu:main'}],
            ]
        }
        bot.send_message(chat_id, '🧾 Управление заказами', reply_markup=keyboard)

    def _send_consultations_menu(self, bot, chat_id):
        keyboard = {
            'inline_keyboard': [
                [{'text': 'Новые запросы', 'callback_data': 'consultations:new:1'}],
                [{'text': 'Последние запросы', 'callback_data': 'consultations:recent:1'}],
                [{'text': '⬅️ Главное меню', 'callback_data': 'menu:main'}],
            ]
        }
        bot.send_message(chat_id, '🧑‍⚕️ Запросы на консультацию', reply_markup=keyboard)

    def _send_report_menu(self, bot, chat_id):
        keyboard = {
            'inline_keyboard': [
                [{'text': 'За все время', 'callback_data': 'report:all'}],
                [{'text': 'За последний месяц', 'callback_data': 'report:last30'}],
                [{'text': 'Выбрать период', 'callback_data': 'report:custom'}],
                [{'text': '⬅️ Главное меню', 'callback_data': 'menu:main'}],
            ]
        }
        bot.send_message(chat_id, '📄 Выберите период отчета', reply_markup=keyboard)

    def _send_help(self, bot, chat_id):
        text = (
            'ℹ️ <b>Помощь</b>\n'
            '• Используйте кнопки меню для списка заказов и консультаций.\n'
            '• Кнопки под заказом позволяют менять статус.\n'
            '• Для поиска заказа нажмите «Найти по номеру» и отправьте ID.\n'
            '• Команда /cancel отменяет текущий ввод.\n'
            '• Отчет можно сформировать за нужный период.'
        )
        bot.send_message(chat_id, text, reply_markup={'inline_keyboard': [[{'text': '⬅️ Меню', 'callback_data': 'menu:main'}]]})

    def _send_orders_list(self, bot, chat_id, scope, page=1):
        if scope == 'today':
            today = timezone.localdate()
            queryset = Order.objects.filter(created_at__date=today)
            title = '🧾 Заказы за сегодня'
        else:
            queryset = Order.objects.exclude(status__in=[Order.STATUS_RECEIVED, Order.STATUS_CANCELED])
            title = '🧾 Активные заказы'

        queryset = (
            queryset.select_related('user', 'address')
            .prefetch_related('items__product', 'items__variant')
            .order_by('-created_at')
        )
        total = queryset.count()
        start = (page - 1) * ORDER_PAGE_SIZE
        orders = list(queryset[start:start + ORDER_PAGE_SIZE])
        if not orders:
            bot.send_message(chat_id, f'{title}\nНет заказов.', reply_markup={'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'menu:orders'}]]})
            return

        bot.send_message(chat_id, f'{title} · страница {page}')
        for order in orders:
            bot.send_message(chat_id, self._format_order(order), reply_markup=self._build_status_keyboard(order))

        if start + ORDER_PAGE_SIZE < total:
            keyboard = {
                'inline_keyboard': [
                    [{'text': 'Показать еще', 'callback_data': f'orders:{scope}:{page + 1}'}],
                    [{'text': '⬅️ Назад', 'callback_data': 'menu:orders'}],
                ]
            }
            bot.send_message(chat_id, 'Хотите еще?', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, 'Это все заказы по запросу.', reply_markup={'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'menu:orders'}]]})

    def _send_consultations_list(self, bot, chat_id, scope, page=1):
        if scope == 'new':
            queryset = ConsultationRequest.objects.filter(status=ConsultationRequest.STATUS_NEW)
            title = '🧑‍⚕️ Новые запросы'
        else:
            queryset = ConsultationRequest.objects.all()
            title = '🧑‍⚕️ Последние запросы'

        queryset = queryset.order_by('-created_at')
        total = queryset.count()
        start = (page - 1) * CONSULTATION_PAGE_SIZE
        consultations = list(queryset[start:start + CONSULTATION_PAGE_SIZE])
        if not consultations:
            bot.send_message(chat_id, f'{title}\nЗапросов нет.', reply_markup={'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'menu:consultations'}]]})
            return

        bot.send_message(chat_id, f'{title} · страница {page}')
        for consultation in consultations:
            bot.send_message(
                chat_id,
                self._format_consultation(consultation),
                reply_markup=self._build_consultation_keyboard(consultation),
            )

        if start + CONSULTATION_PAGE_SIZE < total:
            keyboard = {
                'inline_keyboard': [
                    [{'text': 'Показать еще', 'callback_data': f'consultations:{scope}:{page + 1}'}],
                    [{'text': '⬅️ Назад', 'callback_data': 'menu:consultations'}],
                ]
            }
            bot.send_message(chat_id, 'Хотите еще?', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, 'Это все запросы по выборке.', reply_markup={'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'menu:consultations'}]]})

    def _send_stats(self, bot, chat_id):
        today = timezone.localdate()
        today_orders = Order.objects.filter(created_at__date=today)
        today_total = today_orders.aggregate(total=Sum('total')).get('total') or 0
        pending_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
        new_consultations = ConsultationRequest.objects.filter(status=ConsultationRequest.STATUS_NEW).count()
        week_start = today - timedelta(days=6)
        week_total = (
            Order.objects.filter(created_at__date__gte=week_start, created_at__date__lte=today)
            .aggregate(total=Sum('total'))
            .get('total') or 0
        )

        text = (
            '📊 <b>Статистика</b>\n'
            f'• Заказы сегодня: {today_orders.count()} (на {today_total} c.)\n'
            f'• Ожидают обработки: {pending_count}\n'
            f'• Новые консультации: {new_consultations}\n'
            f'• Выручка за 7 дней: {week_total} c.'
        )
        bot.send_message(chat_id, text, reply_markup={'inline_keyboard': [[{'text': '⬅️ Меню', 'callback_data': 'menu:main'}]]})

    def _send_pricelist(self, bot, chat_id):
        cache_key = 'pricelist:telegram'
        pdf_bytes = cache.get(cache_key)
        if not pdf_bytes:
            products = (
                Product.objects.select_related('category')
                .prefetch_related('variants')
                .all()
                .order_by('category__name', 'name')
            )
            pdf_bytes = build_price_list_pdf(products)
            cache.set(cache_key, pdf_bytes, settings.PRICE_LIST_CACHE_TTL)
        caption = f'Прайс-лист от {timezone.localdate():%d.%m.%Y}'
        bot.send_document(chat_id, 'pricelist.pdf', pdf_bytes, caption=caption)

    def _send_report(self, bot, chat_id, start_date=None, end_date=None, period_label='За все время'):
        orders = (
            Order.objects.select_related('user', 'user__profile')
            .prefetch_related('items__product', 'items__variant')
            .order_by('-created_at')
        )
        if start_date and end_date:
            start_dt = timezone.make_aware(datetime.combine(start_date, dt_time.min))
            end_dt = timezone.make_aware(datetime.combine(end_date, dt_time.max))
            orders = orders.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        status_counts = list(
            orders.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        summary = {
            'total_orders': orders.count(),
            'total_amount': orders.aggregate(total=Sum('total')).get('total') or 0,
        }
        pdf_bytes = build_orders_report_pdf(list(orders), period_label, summary, status_counts)
        filename = f'report-{timezone.localdate():%Y%m%d}.pdf'
        bot.send_document(chat_id, filename, pdf_bytes, caption='Отчет по заказам')

    def _format_order(self, order):
        profile = getattr(order.user, 'profile', None)
        client_name = profile.full_name if profile and profile.full_name else order.user.username
        phone = profile.phone if profile and profile.phone else '-'
        clinic = profile.clinic_name if profile and profile.clinic_name else '-'
        address = order.address.line1 if order.address else '-'
        created_at = timezone.localtime(order.created_at).strftime('%d.%m.%Y %H:%M')
        lines = [
            f'🧾 <b>Заказ #{order.id}</b>',
            f'👤 Клиент: {html.escape(client_name)}',
            f'📞 Телефон: {html.escape(phone)}',
            f'🏥 Организация: {html.escape(clinic)}',
            f'📍 Адрес: {html.escape(address)}',
            f'💳 Сумма: {order.total} c.',
            f'📌 Статус: {STATUS_LABELS.get(order.status, order.status)}',
            f'🕒 Дата: {created_at}',
            '📦 Позиции:',
        ]
        for item in order.items.all():
            variant_label = ''
            if getattr(item, 'variant', None):
                parts = []
                if item.variant.name:
                    parts.append(f'Вариант: {item.variant.name}')
                color = (item.variant.attributes or {}).get('color')
                if color:
                    parts.append(f'Цвет: {color}')
                if parts:
                    variant_label = f" ({', '.join(parts)})"
            lines.append(f'• {html.escape(item.product.name)}{variant_label} x{item.quantity}')
        return '\n'.join(lines)

    def _format_consultation(self, consultation):
        created_at = timezone.localtime(consultation.created_at).strftime('%d.%m.%Y %H:%M')
        status_label = 'Новый' if consultation.status == ConsultationRequest.STATUS_NEW else 'Обработан'
        lines = [
            f'🧑‍⚕️ <b>Запрос консультации #{consultation.id}</b>',
            f'👤 Имя: {html.escape(consultation.name)}',
            f'📞 Телефон: {html.escape(consultation.phone)}',
            f'📌 Статус: {status_label}',
            f'🕒 Дата: {created_at}',
        ]
        if consultation.page_url:
            lines.append(f'🔗 Страница: {html.escape(consultation.page_url)}')
        if consultation.message:
            lines.append(f'💬 Комментарий: {html.escape(consultation.message)}')
        return '\n'.join(lines)

    def _build_status_keyboard(self, order):
        options = STATUS_TRANSITIONS.get(order.status, [])
        if not options:
            return {'inline_keyboard': [[{'text': '⬅️ К заказам', 'callback_data': 'menu:orders'}]]}
        rows = []
        current_row = []
        for status_value in options:
            current_row.append(
                {'text': STATUS_BUTTONS.get(status_value, status_value), 'callback_data': f'order:status:{order.id}:{status_value}'}
            )
            if len(current_row) == 2:
                rows.append(current_row)
                current_row = []
        if current_row:
            rows.append(current_row)
        rows.append([{'text': '⬅️ К заказам', 'callback_data': 'menu:orders'}])
        return {'inline_keyboard': rows}

    def _build_consultation_keyboard(self, consultation):
        if consultation.status == ConsultationRequest.STATUS_DONE:
            return {'inline_keyboard': [[{'text': '⬅️ К списку', 'callback_data': 'menu:consultations'}]]}
        return {
            'inline_keyboard': [
                [{'text': '✅ Закрыть запрос', 'callback_data': f'consultation:done:{consultation.id}'}],
                [{'text': '⬅️ К списку', 'callback_data': 'menu:consultations'}],
            ]
        }

    def _parse_period(self, text):
        normalized = text.replace('—', '-').replace('–', '-')
        if '-' not in normalized:
            return None
        parts = [part.strip() for part in normalized.split('-', 1)]
        if len(parts) != 2:
            return None
        try:
            start_date = datetime.strptime(parts[0], '%d.%m.%Y').date()
            end_date = datetime.strptime(parts[1], '%d.%m.%Y').date()
        except ValueError:
            return None
        if end_date < start_date:
            return None
        return start_date, end_date
