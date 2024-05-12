import logging
import re
import paramiko, os
import psycopg2

from psycopg2 import Error
from dotenv import load_dotenv
from telegram import Update, ForceReply, ReplyKeyboardMarkup, Message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()
TOKEN = os.getenv('TOKEN')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def SQLcmd_ins(command: str, tab_col: str):
    connection = None
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    isSuc = False
    try:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)

        cursor = connection.cursor()
        cmdx = f"INSERT INTO {tab_col} VALUES ('{command}');"
        cursor.execute(cmdx)
        connection.commit()
        logging.info("Команда успешно выполнена")
        isSuc = True
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        isSuc = False
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
            return isSuc


def findPhoneNumberCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_number'


def findPhoneNumber(update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    with open('nums.txt', 'w') as f:
        f.writelines(f"{item}," for item in phoneNumberList)
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
    phoneNumbers += '\nЗаписать эти номера в базу данных?'
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    return 'insert_number'

def InsertNumber(update: Update, context):
    user = update.message.text
    file1 = open("nums.txt", "r")
    lines = file1.read()
    listing = []
    listing = lines.split(",")
    listing.pop()
    file1.close()
    if(user=='Да'):
        tab_col = "PhoneNums (PhoneNum)"
        for num in listing:
            isSuc = SQLcmd_ins(num, tab_col)
        if isSuc:
            update.message.reply_text("Номера успешно записаны!")
            return ConversationHandler.END
        else:
            update.message.reply_text("Ошибка записи номеров!")
            return ConversationHandler.END
    else:
        return ConversationHandler.END

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска emails: ')

    return 'find__email'

def findEmail(update: Update, context):
    user_input = update.message.text
    email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

    email_list = email_regex.findall(user_input)

    if not email_list:
        update.message.reply_text('Emails не найдены')
        return ConversationHandler.END
    with open('emails.txt', 'w') as f:
        f.writelines(f"{item}," for item in email_list)
    Emails = ''
    for i in range(len(email_list)):
        Emails += f'{i+1}. {email_list[i]}\n'
    Emails += '\nЗаписать эти emails в базу данных?'
    update.message.reply_text(Emails) # Отправляем сообщение пользователю
    return 'insert_emails'

def InsertEmail(update: Update, context):
    user = update.message.text
    file1 = open("emails.txt", "r")
    lines = file1.read()
    listing = []
    listing = lines.split(",")
    listing.pop()
    file1.close()
    if(user=='Да'):
        tab_col = "Emails (Email)"
        for email in listing:
            isSuc = SQLcmd_ins(email, tab_col)
        if isSuc:
            update.message.reply_text("Emails успешно записаны!")
            return ConversationHandler.END
        else:
            update.message.reply_text("Ошибка записи emails!")
            return ConversationHandler.END
    else:
        return ConversationHandler.END

def verifyPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')

    return 'verify_password'

def verifyPass(update: Update, context):
    user_input = update.message.text
    password_regex = re.compile(r'^(?=.*[0-9].*)(?=.*[a-z].*)(?=.*[A-Z].*)(?=.*[$!@#%^&*()].*)[0-9a-zA-Z$!@#%^&*()]{8,}$')

    passwd = password_regex.search(user_input)

    if (passwd == None):
        update.message.reply_text('Пароль простой')
    else:
        update.message.reply_text('Пароль сложный')

    return ConversationHandler.END

def LinuxCMD(command: str, isSQL=False):
    load_dotenv()
    host = os.getenv('HOST')
    username = os.getenv('RM_USER')
    port = os.getenv('RM_PORT')
    password = os.getenv('RM_PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return(data)

def get_release(update: Update, context):
    data = LinuxCMD('lsb_release -a')
    update.message.reply_text(data)

def get_uptime(update: Update, context):
    data = LinuxCMD('uptime')
    update.message.reply_text(data)

def get_df(update: Update, context):
    data = LinuxCMD('df')
    update.message.reply_text(data)

def get_uname(update: Update, context):
    data = LinuxCMD('uname -a')
    update.message.reply_text(data)

def get_free(update: Update, context):
    data = LinuxCMD('free -h')
    update.message.reply_text(data)

def get_mpstat(update: Update, context):
    data = LinuxCMD('mpstat')
    update.message.reply_text(data)

def get_w(update: Update, context):
    data = LinuxCMD('w')
    update.message.reply_text(data)

def get_auths(update: Update, context):
    data = LinuxCMD('last -10')
    update.message.reply_text(data)

def get_critical(update: Update, context):
    data = LinuxCMD('journalctl -p crit -n 5')
    update.message.reply_text(data)

def get_ps(update: Update, context):
    data = LinuxCMD('ps -A u | head -n 10')
    update.message.reply_text(data)

def get_ss(update: Update, context):
    data = LinuxCMD('ss -tlp')
    update.message.reply_text(data)

def get_apt_list_all(update: Update, context):
    data = LinuxCMD('apt list --installed | head -n 30')
    update.message.reply_text(data)

def get_apt_list_name_cmd(update: Update, context):
    update.message.reply_text('Введите название пакета: ')

    return 'get_apt_list_name'

def get_apt_list_name(update: Update, context):
    user_input = update.message.text
    input = 'apt list --installed | grep ' + user_input
    data = LinuxCMD(input)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_services(update: Update, context):
    data = LinuxCMD('service --status-all')
    update.message.reply_text(data)

def get_repl_logs(update: Update, context):
    data = LinuxCMD('docker logs db-image', True)
    rdata = LinuxCMD('docker logs db-repl-image', True)
    listing = []
    rlogs = []
    listing = data.split("\n")
    rlogs = rdata.split("\n")
    info = 'DB logs:\n'
    for string in listing:
        if(string.find('repl') != -1):
            info +=f'{string}\n'
    info += 'DB repl logs:\n'
    for string in rlogs:
        if(string.find('repl') != -1):
            info +=f'{string}\n'
    update.message.reply_text(info)


def SQLcmd_sel(command: str):
    connection = None
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')

    try:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)

        cursor = connection.cursor()
        cursor.execute(command)
        data = cursor.fetchall() 
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    return(data)

def get_emails(update: Update, context):
    data = SQLcmd_sel('SELECT * FROM Emails;')
    Emails = ''
    for i in range(len(data)):
        Emails += f'{i+1}. {data[i][1]}\n'
    update.message.reply_text(Emails)

def get_phone_numbers(update: Update, context):
    data = SQLcmd_sel('SELECT * FROM PhoneNums;')
    PNums = ''
    for i in range(len(data)):
        PNums += f'{i+1}. {data[i][1]}\n'
    update.message.reply_text(PNums)

def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    # Обработчик диалога
    convHandlerFindPhoneNumber = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumberCommand)],
        states={
            'find_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumber)],
            'insert_number': [MessageHandler(Filters.text & ~Filters.command, InsertNumber)],
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find__email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'insert_emails': [MessageHandler(Filters.text & ~Filters.command, InsertEmail)],
        },
        fallbacks=[]
    )

    convHandlerVerPass = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPassCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPass)],
        },
        fallbacks=[]
    )

    convHandlerGetAptListName = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list_name', get_apt_list_name_cmd)],
        states={
            'get_apt_list_name': [MessageHandler(Filters.text & ~Filters.command, get_apt_list_name)],
        },
        fallbacks=[]
    )

    
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_apt_list_all", get_apt_list_all))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(convHandlerFindPhoneNumber)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerPass)
    dp.add_handler(convHandlerGetAptListName)
		
	# Регистрируем обработчик текстовых сообщений
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
