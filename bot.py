import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, ADMIN_ID
import database as db

db.init_db()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_broadcast = State()

carts = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    db.add_user(message.from_user.id)
    
    kb = [
        [types.KeyboardButton(text="🍽 Открыть меню ресторана")],
        [types.KeyboardButton(text="🛒 Моя корзина")]
    ]
    if message.from_user.id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="📢 Сделать рекламную рассылку")])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! 👋\nДобро пожаловать в наш премиальный ресторан.\nВыберите действие ниже:",
        reply_markup=keyboard
    )

@dp.message(F.text == "🍽 Открыть меню ресторана")
async def show_categories(message: types.Message):
    kb = [
        [types.InlineKeyboardButton(text="🍔 Фастфуд и Бургеры", callback_data="cat_fastfood")],
        [types.InlineKeyboardButton(text="🐟 Основные блюда (Лосось, Стейки)", callback_data="cat_main")],
        [types.InlineKeyboardButton(text="🥗 Салаты", callback_data="cat_salads")],
        [types.InlineKeyboardButton(text="🍨 Мороженое и Десерты", callback_data="cat_desserts")],
        [types.InlineKeyboardButton(text="🥤 Напитки", callback_data="cat_drinks")],
        [types.InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="view_cart")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("📂 **Категории меню:**\nВыберите интересующий раздел:", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_items(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    
    if cat == "fastfood":
        items = [
            ("Двойной Чизбургер", 35000),
            ("Биг Дёнер", 30000),
            ("Картофель Фри", 15000),
            ("Хот-дог классический", 20000),
            ("Чикенбургер", 28000)
        ]
        title = "🍔 **Фастфуд и Бургеры:**"
    elif cat == "main":
        items = [
            ("Стейк из лосося на гриле", 95000),
            ("Стейк Рибай из говядины", 120000),
            ("Куриное филе с травами", 65000),
            ("Баранребра на мангале", 110000)
        ]
        title = "🐟 **Основные блюда от шеф-повара:**"
    elif cat == "salads":
        items = [
            ("Греческий салат", 45000),
            ("Цезарь с креветками", 60000),
            ("Цезарь с курицей", 50000),
            ("Салат Оливье праздничный", 35000)
        ]
        title = "🥗 **Свежие салаты:**"
    elif cat == "desserts":
        items = [
            ("Мороженое шоколадное пломбир", 20000),
            ("Мороженое ванильное с ягодным сиропом", 25000),
            ("Мороженое фисташковое премиум", 28000),
            ("Торт Наполеон", 35000),
            ("Чизкейк Нью-Йорк", 40000)
        ]
        title = "🍨 **Мороженое и десерты:**"
    else:
        items = [
            ("Лимонад домашний 0.5L", 22000),
            ("Кофе Американо", 15000),
            ("Сок апельсиновый фреш", 30000),
            ("Холодный чай с лимоном", 18000)
        ]
        title = "🥤 **Напитки:**"

    kb = []
    for name, price in items:
        kb.append([types.InlineKeyboardButton(text=f"➕ {name} — {price} сум", callback_data=f"add_{name}_{price}")])
    
    kb.append([types.InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_to_cats")])
    kb.append([types.InlineKeyboardButton(text="🛒 Посмотреть корзину", callback_data="view_cart")])
    
    await callback.message.edit_text(title, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_cats")
async def back_to_cats(callback: types.CallbackQuery):
    kb = [
        [types.InlineKeyboardButton(text="🍔 Фастфуд и Бургеры", callback_data="cat_fastfood")],
        [types.InlineKeyboardButton(text="🐟 Основные блюда (Лосось, Стейки)", callback_data="cat_main")],
        [types.InlineKeyboardButton(text="🥗 Салаты", callback_data="cat_salads")],
        [types.InlineKeyboardButton(text="🍨 Мороженое и Десерты", callback_data="cat_desserts")],
        [types.InlineKeyboardButton(text="🥤 Напитки", callback_data="cat_drinks")],
        [types.InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="view_cart")]
    ]
    await callback.message.edit_text("📂 **Категории меню:**\nВыберите интересующий раздел:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    price = int(parts[-1])
    item_name = "_".join(parts[1:-1])
    
    user_id = callback.from_user.id
    if user_id not in carts:
        carts[user_id] = {}
        
    if item_name in carts[user_id]:
        carts[user_id][item_name]["qty"] += 1
    else:
        carts[user_id][item_name] = {"price": price, "qty": 1}
        
    await callback.answer(f"✅ Добавлено: {item_name}")

@dp.callback_query(F.data == "view_cart")
@dp.message(F.text == "🛒 Моя корзина")
async def show_cart(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    message = event.message if isinstance(event, types.CallbackQuery) else event
    
    if user_id not in carts or not carts[user_id]:
        text = "🛒 Ваша корзина пуста.\nВыберите блюда из меню ресторана!"
        kb = [[types.InlineKeyboardButton(text="🍽 Открыть меню", callback_data="back_to_cats")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        if isinstance(event, types.CallbackQuery):
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
        return

    text = "🛒 **Ваша корзина заказа:**\n\n"
    total_price = 0
    kb = []
    
    for name, info in carts[user_id].items():
        subtotal = info["price"] * info["qty"]
        total_price += subtotal
        text += f"▪️ **{name}** x {info['qty']} шт. = {subtotal} сум\n"
        kb.append([
            types.InlineKeyboardButton(text=f"❌ Удалить {name}", callback_data=f"cart_del_{name}"),
            types.InlineKeyboardButton(text="➕", callback_data=f"cart_plus_{name}"),
            types.InlineKeyboardButton(text="➖", callback_data=f"cart_minus_{name}")
        ])
        
    text += f"\n💰 **Итого к оплате: {total_price} сум**"
    
    kb.append([types.InlineKeyboardButton(text="✅ Подтвердить и оформить заказ", callback_data="checkout")])
    kb.append([types.InlineKeyboardButton(text="🍽 Добавить еще блюда", callback_data="back_to_cats")])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    if isinstance(event, types.CallbackQuery):
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cart_"))
async def modify_cart(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    item_name = "_".join(parts[2:])
    user_id = callback.from_user.id
    
    if user_id in carts and item_name in carts[user_id]:
        if action == "plus":
            carts[user_id][item_name]["qty"] += 1
        elif action == "minus":
            carts[user_id][item_name]["qty"] -= 1
            if carts[user_id][item_name]["qty"] <= 0:
                del carts[user_id][item_name]
        elif action == "del":
            del carts[user_id][item_name]
            
    await show_cart(callback)
    await callback.answer()

@dp.callback_query(F.data == "checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in carts or not carts[user_id]:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
        return
        
    await state.set_state(OrderState.waiting_for_phone)
    phone_kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.answer("📞 Пожалуйста, отправьте ваш номер телефона для связи:", reply_markup=phone_kb)
    await callback.answer()

@dp.message(OrderState.waiting_for_phone, F.contact | F.text)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    await state.set_state(OrderState.waiting_for_address)

    geo_kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📍 Отправить геопозицию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("📍 Теперь отправьте вашу геопозицию на карте или напишите адрес доставки текстом:", reply_markup=geo_kb)

@dp.message(OrderState.waiting_for_address)
async def finalize_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    address_text = "Геопозиция прикреплена" if message.location else message.text
    
    user_cart = carts.get(user_id, {})
    items_summary = ""
    total_price = 0
    
    for name, info in user_cart.items():
        subtotal = info["price"] * info["qty"]
        total_price += subtotal
        items_summary += f"• {name} x {info['qty']} шт. ({subtotal} сум)\n"
        
    order_id = db.add_order(
        user_id=user_id,
        user_name=message.from_user.full_name,
        phone=data['phone'],
        items_text=items_summary,
        total_price=total_price
    )
    
    carts[user_id] = {}

    main_kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍽 Открыть меню ресторана")],
            [types.KeyboardButton(text="🛒 Моя корзина")]
        ], 
        resize_keyboard=True
    )
    
    await message.answer(
        f"✅ **Заказ №{order_id} успешно оформлен!**\n\n"
        f"📋 **Состав заказа:**\n{items_summary}\n"
        f"💰 **Общая сумма: {total_price} сум**\n\n"
        "Кухня уже приняла ваш заказ в работу!",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

    admin_text = (
        f"🚨 **НОВЫЙ ЗАКАЗ В РЕСТОРАНЕ №{order_id}**\n"
        f"👤 Гость: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📞 Тел: `{data['phone']}`\n"
        f"📍 Адрес: {address_text}\n\n"
        f"🛒 **Заказ:**\n{items_summary}\n"
        f"💰 **Сумма:** {total_price} сум"
    )

    admin_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👨‍🍳 Готовится", callback_data=f"status_cook_{order_id}_{user_id}"),
            types.InlineKeyboardButton(text="🛵 Доставляется", callback_data=f"status_road_{order_id}_{user_id}")
        ],
        [
            types.InlineKeyboardButton(text="✅ Выполнен", callback_data=f"status_done_{order_id}_{user_id}"),
            types.InlineKeyboardButton(text="❌ Отменить", callback_data=f"status_cancel_{order_id}_{user_id}")
        ]
    ])

    try:
        if message.location:
            await bot.send_location(ADMIN_ID, message.location.latitude, message.location.longitude)
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_kb, parse_mode="Markdown")
        print(f"✅ Заказ №{order_id} отправлен администратору!")
    except Exception as e:
        print(f"❌ Ошибка отправки админу: {e}")

    await state.clear()

@dp.message(F.text == "📢 Сделать рекламную рассылку", F.from_user.id == ADMIN_ID)
async def start_broadcast(message: types.Message, state: FSMContext):
    await state.set_state(OrderState.waiting_for_broadcast)
    await message.answer("📢 Введите рекламный текст или отправьте пост (с картинкой/кнопками), который хотите разослать всем пользователям бота:")

@dp.message(OrderState.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def send_broadcast(message: types.Message, state: FSMContext):
    users = db.get_all_users()
    success = 0
    fail = 0
    
    await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    
    for uid in users:
        try:
            await message.send_copy(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            
    await message.answer(f"✅ **Рассылка завершена!**\nУспешно отправлено: {success}\nНе удалось: {fail}", parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data.startswith("status_"))
async def update_order_status(callback: types.CallbackQuery):
    _, action, order_id, client_id = callback.data.split("_")
    client_id = int(client_id)

    status_info = {
        "cook": ("👨‍🍳 Готовится", "Ваш заказ №{} готовится на кухне шеф-поваром!"),
        "road": ("🛵 Доставляется", "Курьер доставляет ваш заказ №{}! 🛵"),
        "done": ("✅ Выполнен", "Заказ №{} доставлен. Приятного аппетита! 🍷"),
        "cancel": ("❌ Отменен", "К сожалению, заказ №{} был отменен рестораном.")
    }

    title, client_text = status_info[action]
    db.update_status(order_id, title)

    try:
        await bot.send_message(client_id, f"🔔 **Статус заказа обновлен:**\n" + client_text.format(order_id), parse_mode="Markdown")
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + f"\n\nСтатус: **{title}**",
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown"
    )
    await callback.answer(f"Статус изменен на {title}")

async def main():
    print("🚀 Масштабный ресторанный бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())