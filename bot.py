import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ── إعدادات عامة ──
# اقرأ التوكن و Admin Chat ID من متغيرات البيئة لتجنب تخزينها في الكود
TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))
if not TOKEN or not ADMIN_CHAT_ID:
    raise RuntimeError("TOKEN and ADMIN_CHAT_ID must be set as environment variables.")

AFFILIATE_LINK = os.environ.get("AFFILIATE_LINK", "https://refpa3740576.top/L?tag=d_4354442m_4129c_&site=4354442&ad=4129")

VODAFONE_NUMBER = os.environ.get("VODAFONE_NUMBER", "01055001212")
WITHDRAW_ADDRESS = os.environ.get("WITHDRAW_ADDRESS", "Egypt, Abou Reddis, Ash Store")

# ── حالات المحادثة ──
CHOOSING, DEP_AMT, DEP_PHONE, DEP_SCREEN, DEP_PLAYER, \
WIT_WALLET, WIT_PLAYER_ID, WIT_AMOUNT, WIT_CODE = range(9)

# ── لوحة الخيارات ──
def choice_keyboard():
    keyboard = [["💸 إيداع"], ["🏧 سحب"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

# ── دوال البوت ──
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ تنويه: الشركة غير مسؤولة عن أي طلب غير مستوفي البيانات.")
    await update.message.reply_text("👇 اختر العملية:", reply_markup=choice_keyboard())
    return CHOOSING

# ==== إيداع ==== 
async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💵 للإيداع: حوال المبلغ عبر فودافون كاش إلى {VODAFONE_NUMBER}\n\n"
        "1⃣ أدخل مبلغ الإيداع:",
        reply_markup=ReplyKeyboardRemove()
    )
    return DEP_AMT

async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("🚨 يرجى إدخال رقم صالح للمبلغ.")
        return DEP_AMT
    context.user_data['amount'] = text
    await update.message.reply_text("2⃣ أدخل رقم الهاتف الذي أرسلت منه المبلغ:")
    return DEP_PHONE

async def deposit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    # validate phone
    if not phone.isdigit() or len(phone) < 8:
        await update.message.reply_text("🚨 يرجى إدخال رقم هاتف صالح.")
        return DEP_PHONE
    context.user_data['phone'] = phone
    await update.message.reply_text("3⃣ أرسل لقطة شاشة تؤكد التحويل:")
    return DEP_SCREEN

async def deposit_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("🚨 يرجى إرسال صورة فقط.")
        return DEP_SCREEN
    context.user_data['screenshot_id'] = update.message.photo[-1].file_id
    await update.message.reply_text("4⃣ أدخل كود اللاعب (Player ID):")
    return DEP_PLAYER

async def deposit_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = update.message.text.strip()
    if not pid:
        await update.message.reply_text("🚨 يرجى إدخال كود لاعب صالح.")
        return DEP_PLAYER
    context.user_data['player_id'] = pid

    # إرسال للأدمن
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "📥 طلب إيداع جديد:\n"
            f"➡️ Player ID: {context.user_data['player_id']}\n"
            f"➡️ المبلغ: {context.user_data['amount']}\n"
            f"➡️ رقم الهاتف: {context.user_data['phone']}"
        )
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=context.user_data['screenshot_id']
    )

    # رسالة شكر للمستخدم
    button = InlineKeyboardButton("🎁 العب الآن عبر التطبيق الرسمي", url=AFFILIATE_LINK)
    await update.message.reply_text(
        "🎉 تم استلام طلبك بنجاح!", reply_markup=InlineKeyboardMarkup([[button]])
    )
    await update.message.reply_text("🔄 هل ترغب في عملية أخرى؟", reply_markup=choice_keyboard())
    return CHOOSING

# ==== سحب ==== 
async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏧 عنوان السحب:\n📍 {WITHDRAW_ADDRESS}\n\n1⃣ أدخل رقم محفظة فودافون كاش:",
        reply_markup=ReplyKeyboardRemove()
    )
    return WIT_WALLET

async def withdraw_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    if not wallet.isdigit():
        await update.message.reply_text("🚨 يرجى إدخال رقم محفظة صالح.")
        return WIT_WALLET
    context.user_data['withdraw_wallet'] = wallet
    await update.message.reply_text("2⃣ أدخل كود اللاعب (Player ID):")
    return WIT_PLAYER_ID

async def withdraw_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = update.message.text.strip()
    if not pid:
        await update.message.reply_text("🚨 يرجى إدخال كود لاعب صالح.")
        return WIT_PLAYER_ID
    context.user_data['withdraw_player_id'] = pid
    await update.message.reply_text("3⃣ أدخل المبلغ المطلوب سحبه:")
    return WIT_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = update.message.text.strip()
    if not amt.isdigit():
        await update.message.reply_text("🚨 يرجى إدخال مبلغ رقمي صالح.")
        return WIT_AMOUNT
    context.user_data['withdraw_amount'] = amt
    await update.message.reply_text("4⃣ أدخل كود السحب:")
    return WIT_CODE

async def withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not code:
        await update.message.reply_text("🚨 يرجى إدخال كود صالح.")
        return WIT_CODE
    context.user_data['withdraw_code'] = code

    # إرسال للأدمن
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "📤 طلب سحب جديد:\n"
            f"➡️ محفظة: {context.user_data['withdraw_wallet']}\n"
            f"➡️ Player ID: {context.user_data['withdraw_player_id']}\n"
            f"➡️ المبلغ: {context.user_data['withdraw_amount']}\n"
            f"➡️ كود السحب: {context.user_data['withdraw_code']}"
        )
    )
    # رسالة شكر للمستخدم
    button = InlineKeyboardButton("🎁 العب الآن عبر التطبيق الرسمي", url=AFFILIATE_LINK)
    await update.message.reply_text(
        "🎉 تم استلام طلبك بنجاح!", reply_markup=InlineKeyboardMarkup([[button]])
    )
    await update.message.reply_text("🔄 هل ترغب في عملية أخرى؟", reply_markup=choice_keyboard())
    return CHOOSING

# دالة لإدارة الأخطاء
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.getLogger(__name__).error(f"Update {update} caused error {context.error}")
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="🚨 الوكيل لا يعمل في الوقت الحالي.")
    if update and update.message:
        await update.message.reply_text("🚨 الوكيل لا يعمل في الوقت الحالي، يرجى المحاولة لاحقاً.")

# ── تشغيل البوت ──
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error)
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^💸 إيداع$'), deposit_start), MessageHandler(filters.Regex('^🏧 سحب$'), withdraw_start)],
        states={
            CHOOSING: [MessageHandler(filters.Regex('^💸 إيداع$'), deposit_start), MessageHandler(filters.Regex('^🏧 سحب$'), withdraw_start)],
            DEP_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)],
            DEP_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_phone)],
            DEP_SCREEN: [MessageHandler(filters.PHOTO, deposit_screen)],
            DEP_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_player)],
            WIT_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_wallet)],
            WIT_PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_player_id)],
            WIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount)],
            WIT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_code)],
        },
        fallbacks=[],
    )
    app.add_handler(conv)
    print("✅ Bot is running...")
    app.run_polling()
