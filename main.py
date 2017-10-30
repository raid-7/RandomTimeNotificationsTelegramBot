import telebot
import threading
import time
import internal as feat
import re
import signal


PROCESS_INTERVAL = 10
WEEK_INTERVAL = 60*60*24*7
allow_work = True

def sigterm(*args):
    global allow_work
    allow_work = False

signal.signal(signal.SIGTERM, sigterm)


token = ''
dropbox_token = ''
with open('token.info', 'rt') as f, open('dropbox.info', 'rt') as df:
    token = f.read()
    token = token.strip()
    dropbox_token = df.read()
    dropbox_token = dropbox_token.strip()
    
if not token or not dropbox_token:
    exit(0)
    
filesys = feat.DropboxFileSystem(dropbox_token, 'very_important_file.info')
timesys = feat.TimeSystem(filesys)
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['help', 'start'])
def msg_start(message):
    bot.send_message(message.chat.id, "This bot can send you notifications"+
                        " at random time with defined average frequency\n"+
                     "Commands:\n"+
                     "/help - prints help\n"+
                     "/list - list of your notification lines\n"+
                     "/add [average times per week] [message] - add new notification line\n"+
                     "/rm [id] - removes notification line")
    
@bot.message_handler(commands=['add'])
def msg_add_line(message):
    chat_id = message.chat.id
    match = re.match(r'^\s*/add\s+(\d+)(\s.+)?$', message.text.strip())
    if not match or not match.group(2):
        bot.send_message(chat_id, 'Wrong syntax!')
        return
    
    text = [match.group(1), match.group(2).strip()]
    if not text[1]:
        bot.send_message(chat_id, 'Wrong syntax!')
        return 
    
    freq = int(text[0]) / WEEK_INTERVAL * PROCESS_INTERVAL
    if freq > 1.0:
        freq = 1.0
    
    iid = timesys.register_line(chat_id, freq, text[1])
    bot.send_message(chat_id, "Added notification line {:d}".format(iid))
    
    
@bot.message_handler(commands=['rm'])
def msg_remove_line(message):
    text = re.split(r'\s+', message.text.strip())
    chat_id = message.chat.id
    if len(text) != 2 or not text[1].isdigit():
        bot.send_message(chat_id, 'Wrong syntax!')
        return
    
    iid = int(text[1])
    line = timesys.get_line(iid)
    if line in timesys.get_user_lines(chat_id) and timesys.unregister_line(iid):
        bot.send_message(chat_id, "Removed notification line {:d}".format(iid))
    else:
        bot.send_message(chat_id, "Wrong id!".format(iid))
        
        

@bot.message_handler(commands=['list'])
def msg_list_lines(message):
    chat_id = message.chat.id
    if message.text.strip() != '/list':
        bot.send_message(chat_id, 'Wrong syntax!')
        return
    
    lst = timesys.get_user_lines(chat_id)
    lst = ["{:d} {:d} {:s}" \
                .format(t.internal_id, round(t.frequency * WEEK_INTERVAL / PROCESS_INTERVAL), t.message)
           for t in lst]
    bot.send_message(chat_id,
                "Your lines (id, average times per week, message):\n{:s}".format('\n'.join(lst)))

def start_polling():
    bot.polling()

polling_thread = threading.Thread(target=start_polling)
polling_thread.start()

while allow_work:
    time.sleep(PROCESS_INTERVAL)
    lines = timesys.process()
    
    for line in lines:
        bot.send_message(line.chat_id, line.message, disable_notification=False)

bot.stop_polling()
timesys.save()
