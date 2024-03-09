import telebot
import tempfile
import uuid
import threading
import convertapi
import os

# Telegram Bot Token
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# ConvertAPI Secret Key
convertapi.api_secret = 'YOUR_CONVERT_API_SECRET'

# Initialize the Telegram Bot
bot = telebot.TeleBot(TOKEN)

# Dictionary to store users' preferred language
users_language = {}

# Function to convert PDF to DOCX and send the converted file
def convert_pdf_to_docx_and_send(chat_id, pdf_path, docx_path, order_number):
    try:
        # Convert PDF to DOCX using ConvertAPI
        convertapi.convert('docx', {'File': pdf_path}, from_format='pdf').save_files(docx_path)
        
        # Prepare caption message based on user's language preference
        caption = {
            'ar': f"تم تحويل الملف بنجاح! 🎉 يمكنك تنزيل الملف المحول أدناه.\nAdmin: @od_331 - Ahmed",
            'en': f"Your file has been successfully converted! 🎉 You can download the converted file below.\nAdmin: @od_331 - Ahmed"
        }[users_language.get(chat_id, 'ar')]
        
        # Send the converted DOCX file with caption
        with open(docx_path, 'rb') as docx_file:
            bot.send_document(chat_id, docx_file, caption=caption)
        
        # Remove the temporary PDF and DOCX files
        os.remove(pdf_path)
        os.remove(docx_path)
    except Exception as e:
        # Handle conversion errors
        error_message = {
            'ar': f"حدث خطأ أثناء تحويل الملف: {e}. الرجاء مراسلة الإدارة.",
            'en': f"An error occurred during file conversion: {e}. Please contact the admin."
        }[users_language.get(chat_id, 'ar')]
        bot.reply_to(chat_id, error_message)

# Command handler for '/start' command
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in users_language:
        # Prompt user to select conversation language
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('عربي', 'English')
        msg = bot.reply_to(message, "اختر لغة المحادثة / Choose conversation language:", reply_markup=markup)
        bot.register_next_step_handler(msg, set_language)
    else:
        send_welcome(message, users_language[chat_id])

# Function to set user's language preference
def set_language(message):
    chat_id = message.chat.id
    users_language[chat_id] = 'ar' if message.text == 'عربي' else 'en'
    send_welcome(message, users_language[chat_id])

# Function to send welcome message based on user's language preference
def send_welcome(message, language):
    welcome_message = {
        'ar': "أهلاً بك في بوت تحويل PDF إلى Word. أرسل لي ملف PDF لتحويله.\nAdmin: @od_331 - Ahmed",
        'en': "Welcome to the PDF to Word conversion bot. Please send me a PDF file to convert.\nAdmin: @od_331 - Ahmed"
    }[language]
    bot.send_message(message.chat.id, welcome_message)

# Handler for document messages (PDF files)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Create a temporary file to save the downloaded PDF
    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_temp.write(downloaded_file)
    pdf_temp.close()
    
    # Create a temporary file path for the DOCX conversion result
    docx_path = tempfile.mktemp(suffix='.docx')
    
    # Send a processing message based on user's language preference
    processing_message = {
        'ar': "جاري تحويل الملف، الرجاء الانتظار... 🔄",
        'en': "Converting the file, please wait... 🔄"
    }[users_language.get(chat_id, 'ar')]
    bot.send_message(chat_id, processing_message)
    
    # Generate a unique order number
    order_number = uuid.uuid4()
    
    # Start a new thread to perform the conversion and sending
    threading.Thread(target=convert_pdf_to_docx_and_send, args=(chat_id, pdf_temp.name, docx_path, order_number), daemon=True).start()

# Start polling for incoming messages
bot.polling()
