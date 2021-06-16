################################################################################# HEADER
# Creator: @imAvizhen

import time
import random
import logging
import datetime
import itertools
from tinydb import TinyDB, Query
from telegram.utils import helpers
from google_trans_new import google_translator  

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (Updater,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters,
)

# Enable logging (Optional)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)




# Create clients
db   = TinyDB('data.json')
ch   = TinyDB('channels.json')
info = Query()

translator = google_translator()



# information
admin = 225071327
bot_username = 'lezardbot' # without @
public_channel = 'omoomi1' # without @
recaptcha_photos = ['8', '10', '11']

# context

join_in_channel_text = """To continue your activity, please subscribe to the sponsor channel'"""

normal_start_text = """Click the button below to get your link"""

you_are_not_in_the_channel_text = """You are not in the channel !"""

link_text = """https://t.me/{bot_username}?start={user_id}"""
after_send_link_text = "Your link"

first_stage_alert_text = """This person became a member of the robot with your link: """

carefully_text = """Choose more carefully"""

select_answer_text = """Select answer"""

active_user_text = """This person has been added to your subcategories: """

fraud_is_prohibited_text = """You can not become a member with your own link"""

link_sender_text  = """Membership link for one person only.
channel: {channel_number}"""

status_text = """Total usres: {total_users} 
Total bans: {total_bans}
Total channels: {total_channels}
Total subcategories: {total_sub}""" # for admin

not_found_text = """Not found""" # for admin

user_info_text = """ID: [{uid}](tg://user?id={uid})
name: {name}
presenter: [{presenter}](tg://user?id={presenter})
subcategories: {sub}""" # for admin

channel_info_text = """ID: [{channel_id}]({invite_link})
Title: {title}
Count: {count}""" # for admin

select_your_lnaguage_text = """Please select your language..."""

################################################################################## BODY

# select your language
def wath_is_your_lang(update, context):

    bot = context.bot
    user_id = update.effective_user.id

    keyboard = [
        [
            InlineKeyboardButton("English", callback_data='lang - en'),
            InlineKeyboardButton("Farsi", callback_data='lang - fa')
        ],
        [
            InlineKeyboardButton("Russian", callback_data='lang - ru'),
            InlineKeyboardButton("Arabic", callback_data='lang - ar')
        ],
        [
            InlineKeyboardButton("French", callback_data='lang - fr'),
            InlineKeyboardButton("Spanish", callback_data='lang - es')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id = user_id,
        text = select_your_lnaguage_text,
        reply_markup = reply_markup,
        parse_mode = 'Markdown'
    )

# public function for send link to user
def link_sender(context, user_id, channel_id, channel_number):

    bot = context.bot
    invite_link = bot.create_chat_invite_link(chat_id = channel_id, member_limit = 1).invite_link

    keyboard = [
        [
            InlineKeyboardButton("Subscribe", url = invite_link)
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    code = db.search(info.id == user_id)[0]['lang']
    translate_text = translator.translate(link_sender_text.format( channel_number = int(channel_number) ), lang_tgt = code)

    bot.send_message(chat_id = user_id, text = translate_text, reply_markup = reply_markup)

# alert : join in my public channel
def join_in_my_channel(update = 'null', context = 'null', query = 'null'):
    
    if query == 'null':
        user_id = update.effective_user.id
    else:
        user_id = query.message.chat.id

    bot = context.bot
    keyboard = [
        [
            InlineKeyboardButton("Channel", url='https://t.me/%s' % public_channel),
            InlineKeyboardButton("Verify", callback_data='member?')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    code = db.search(info.id == user_id)[0]['lang']
    translate_text = translator.translate(join_in_channel_text, lang_tgt = code)

    bot.send_message(
        chat_id = user_id,
        text = translate_text,
        reply_markup = reply_markup,
        parse_mode = 'Markdown'
    )

# sava userData in tinydb for first time
def insert_for_first_time(update, context, mode = 'normal', presenter = 'null'):
    
    user_id = update.effective_user.id
    fname   = update.effective_user.first_name
    
    if mode == 'guest':
        lang = db.search(info.id == presenter)[0]['lang']
        db.insert({
            'id': user_id,
            'name': fname,
            'lang': lang,
            'subcategories': 0,
            'presenter': presenter,
            'status': 'recaptcha'
        })
        return

    db.insert({
            'id': user_id,
            'name': fname,
            'lang': None,
            'subcategories': 0,
            'presenter': None,
            'status': 'language',
        })

# presenter helper
def presenter_works(query = 'null', context = 'null'):

    bot = context.bot
    user_id = query.message.chat.id
    user_info = db.search(info.id == user_id)[0]

    fname   = user_info['name']
    presenter = user_info['presenter']
    subcategories = db.search(info.id == presenter)[0]['subcategories']

    subcategories += 1
    db.update({'subcategories': subcategories}, info.id == presenter)

    code = db.search(info.id == user_id)[0]['lang']
    translate_text = translator.translate(active_user_text, lang_tgt = code)

    translate_text += "[{name}](tg://user?id={user_id})"

    bot.send_message(chat_id = presenter, text = translate_text.format(name = fname, user_id = user_id), parse_mode = 'Markdown')

    # send link for presenter

    if subcategories >= 2 and subcategories % 2 == 0:
        channel_number = subcategories / 2

        search_for_channel = ch.search(info.number == channel_number)

        if len(search_for_channel) == 0:
            return
        
        channel_id = search_for_channel[0]['id']
        link_sender(context, presenter, channel_id, channel_number)

# normal start
def normal_start(update='null', context='null', query='null'):

    if query == 'null':
        user_id = update.effective_user.id

        code = db.search(info.id == user_id)[0]['lang']
        translate_text = translator.translate(normal_start_text, lang_tgt = code)

        keyboard = [
            [
                InlineKeyboardButton("Get link", callback_data='getlink')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = translate_text, reply_markup = reply_markup)
    else:
        bot = context.bot
        user_id = query.message.chat.id
        get_user_state = db.search(info.id == user_id)[0]['status']

        status = bot.get_chat_member(chat_id = '@' + public_channel, user_id = user_id).status
        
        if status == 'left' or status == 'kicked':
            code = db.search(info.id == user_id)[0]['lang']
            translate_text = translator.translate(you_are_not_in_the_channel_text, lang_tgt = code)
            query.answer(translate_text)
            query.answer()
            return
        
        if get_user_state == 'channel':
            presenter_works(query = query, context = context)
            db.update({'status': 'accepted'}, info.id == user_id)

        query.answer()
        query.message.delete()

        code = db.search(info.id == user_id)[0]['lang']
        translate_text = translator.translate(normal_start_text, lang_tgt = code)

        keyboard = [
            [
                InlineKeyboardButton("Get link", callback_data='getlink')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.reply_text(text = translate_text, reply_markup = reply_markup)

# reCAPTHCHA confirmation
def is_human(query, context):

    bot = context.bot
    user_id = query.message.chat.id
    status = db.search(info.id == user_id)[0]['status']

    if status != 'recaptcha':
        query.message.delete()
        return

    is_join = bot.get_chat_member(chat_id = '@' + public_channel, user_id = user_id).status
        
    if is_join == 'left' or is_join == 'kicked':

        db.update({'status': 'channel'}, info.id == user_id)
        join_in_my_channel(query = query, context = context)
        query.message.delete()
        query.answer()
        return
    
    presenter_works(query = query, context = context)
    normal_start(query = query, context = context)
    db.update({'status': 'accepted'}, info.id == user_id)

# send recaptcha
def send_recaptcha(update, context):
    
    bot = context.bot
    user_id = update.effective_user.id
    
    recaptcha_answer = random.choice(recaptcha_photos)
    list_answers = ['6', '12', '7', '5', '13', '14', '15', '16', '17', '18', '4'] # Prohibited: 8, 10, 11
    new_list_answers = random.sample( list_answers, len(list_answers) )
    a, b, c = new_list_answers[0:3]

    keyboard_array = [
        InlineKeyboardButton(recaptcha_answer, callback_data=str('answer')),
        InlineKeyboardButton(a, callback_data=str('z')),
        InlineKeyboardButton(b, callback_data=str('x')),
        InlineKeyboardButton(c, callback_data=str('y')),
    ]
    new_array = random.sample( keyboard_array, len(keyboard_array) )
    keyboard = [new_array]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard

    code = db.search(info.id == user_id)[0]['lang']
    translate_text = translator.translate(select_answer_text, lang_tgt = code)

    photo = open('./images/%s.jpg' % recaptcha_answer, 'rb')
    bot.send_photo(chat_id = user_id, photo = photo, caption = translate_text, reply_markup = reply_markup)
    photo.close()

# start function
def start(update, context):

    bot = context.bot
    user_id = update.effective_user.id
    search_for_user = db.search(info.id == user_id)

    if len(search_for_user) == 0:
        insert_for_first_time(update, context)
        wath_is_your_lang(update, context)
        return

    user_step = db.search(info.id == user_id)[0]['status']

    if user_step == 'language':
        wath_is_your_lang(update, context)
        return

    if user_step == 'ban':
        return

    if user_step == 'recaptcha':
        send_recaptcha(update, context)
        return

    status = bot.get_chat_member(chat_id = '@' + public_channel, user_id = user_id).status
    if status == 'left' or status == 'kicked':
        join_in_my_channel(update = update, context = context)
        return

    normal_start(update = update, context = context)

# set user language
def set_lang(query, context, lang):

    bot = context.bot
    user_id = query.message.chat.id
    user_status = db.search(info.id == user_id)[0]['status']

    if user_status == 'language':
        db.update({'status': 'accepted'}, info.id == user_id)

    db.update({'lang': lang}, info.id == user_id)
    normal_start(query = query, context = context)

# send link
def link(query, context):
    user_id = query.message.chat.id
    user_status = db.search(info.id == user_id)[0]['status']
    
    unqualify = ['ban', 'channel', 'recaptcha', 'language']
    if user_status in unqualify:
        query.answer()
        return

    code = db.search(info.id == user_id)[0]['lang']
    translate_text = translator.translate(after_send_link_text, lang_tgt = code)

    query.edit_message_text(text = link_text.format(bot_username = bot_username, user_id = user_id))
    query.message.reply_text(translate_text)
    query.answer()

# start from guest
def guest(update, context):

    bot = context.bot
    user_id = update.effective_user.id
    fname   = update.effective_user.first_name
    text = update.message.text
    presenter = text.split(' ')[1]

    try:
        presenter = int(presenter)
    except:
        start(update, context)
        return
    
    if presenter == user_id:
        code = db.search(info.id == user_id)[0]['lang']
        translate_text = translator.translate(fraud_is_prohibited_text, lang_tgt = code)
        update.message.reply_text(translate_text)
        return

    search_for_user = db.search(info.id == user_id)
    search_for_presenter = db.search(info.id == presenter)

    if len(search_for_user) != 0:
        normal_start(update, context)
        return

    if len(search_for_presenter) == 0:
        start(update, context)
        return
    
    presenter_status = search_for_presenter[0]['status']
    if presenter_status == 'ban':
        start(update, context)
        return


    insert_for_first_time(update, context, 'guest', presenter)

    code = db.search(info.id == presenter)[0]['lang']
    translate_text = translator.translate(first_stage_alert_text, lang_tgt = code)

    translate_text += "[{name}](tg://user?id={user_id})"

    bot.send_message(chat_id = presenter, text = translate_text.format(name = fname, user_id = user_id), parse_mode = 'Markdown')
    send_recaptcha(update, context)
  
######################### ADMIN PANEL

def add_channel(update, context):
    
    text = update.message.text
    array_text = text.split(' ')
    try:
        channel_number = int(array_text[1])
        channel_id = int(array_text[2])
    except:
        update.message.reply_text('Error. example: /add 3 -100654844851')
        return


    search_for_channel = ch.search(info.number == channel_number)

    if len(search_for_channel) != 0:
        ch.update({'id': int(channel_id)}, info.number == channel_number)
    else:
        ch.insert({'id': int(channel_id), 'number': int(channel_number)})

    qualify_limit = int(channel_number) * 2
    all_members = db.all()

    count = 0
    for member in all_members:
        user_id = member['id']
        subcategories = member['subcategories']
        if subcategories < qualify_limit:
            continue
        
        count += 1
        link_sender(context, user_id, int(channel_id), int(channel_number))
    
    update.message.reply_text('Ok, send for {} users'.format(count))

def status(update, context):
    
    # all users
    all_usres_in_array = db.all()
    total_users = len(all_usres_in_array)

    # all bans
    all_bans_in_array = db.search(info.status == 'ban')
    total_bans = len(all_bans_in_array)

    # all chnnels
    all_channels_in_array = ch.all()
    totla_channels = len(all_channels_in_array)

    # all subcategories
    total_subcategories = 0
    for member in all_usres_in_array:
        subcategories = member['subcategories']
        total_subcategories += int(subcategories)

    update.message.reply_text(status_text.format(total_users = total_users, total_bans = total_bans, total_channels = totla_channels, total_sub = total_subcategories))

def ban(update, context):
    
    text = update.message.text
    array_text = text.split(' ')
    try:
        ban = int(array_text[1])
    except:
        update.message.reply_text(not_found_text)
        return

    search_for_user = db.search(info.id == ban)

    if search_for_user == 0:
        update.message.reply_text(not_found_text)
        return

    db.update({'status': 'ban'}, info.id == ban)
    update.message.reply_text('Done:)')

def unban(update, context):
    
    text = update.message.text
    array_text = text.split(' ')
    try:
        unban = int(array_text[1])
    except:
        update.message.reply_text(not_found_text)
        return

    search_for_user = db.search(info.id == unban)

    if search_for_user == 0:
        update.message.reply_text(not_found_text)
        return

    db.update({'status': 'accepted'}, info.id == unban)
    update.message.reply_text('Done:)')

def top(update, context):

    text = update.message.text
    array_text = text.split(' ')
    try:
        number = int(array_text[1])
    except:
        update.message.reply_text(not_found_text)
        return

    all_users = db.all()

    if len(all_users) < number:
        update.message.reply_text('تعداد کاربر ها کمتر از درخواست شماست')
        return

    all_usres_dict = dict()
    for user in all_users:
        uid = user['id']
        sub = user['subcategories']
        all_usres_dict[uid] = sub
    
    sort = dict(sorted(all_usres_dict.items(), key=lambda item: item[1]))
    keys = list(sort.keys())
    keys = keys[-number:]

    output = ''
    for user in reversed(keys):
        output += '[{user}](tg://user?id={user}): {value}\n'.format(user = user, value = sort[user])

    update.message.reply_text(output, parse_mode = 'Markdown')

def user(update, context):

    text = update.message.text
    array_text = text.split(' ')
    try:
        user_id = int(array_text[1])
    except:
        update.message.reply_text(not_found_text)
        return

    search_for_user = db.search(info.id == user_id)
    if len(search_for_user) == 0:
        update.message.reply_text(not_found_text)
        return

    user_info = search_for_user[0]
    uid = user_info['id']
    sub = user_info['subcategories']
    presenter = user_info['presenter']
    name = user_info['name']

    update.message.reply_text(user_info_text.format(uid = uid, name = name, presenter = presenter, sub = sub), parse_mode = 'Markdown')

def send(update, context):

    bot = context.bot
    try:
        msg_id = update.message.reply_to_message.message_id
    except:
        update.message.reply_text('Plese reply on message')
        return


    all_users = db.all()
    for user in all_users:
        user_id = user['id']
        status = user['status']

        if user_id == admin:
            continue

        if status == 'ban':
            continue

        bot.copy_message(
            chat_id = user_id,
            from_chat_id = admin,
            message_id = msg_id
        )

    update.message.reply_text("Posted for {} people".format( len(all_users) ))

def chan(update, context):
    
    bot = context.bot
    text = update.message.text
    array_text = text.split(' ')
    try:
        number = int(array_text[1])
    except:
        update.message.reply_text(not_found_text)
        return
    

    search_for_channel = ch.search(info.number == number)

    if len( search_for_channel ) == 0:
        update.message.reply_text(not_found_text)
        return
    
    channel_id = search_for_channel[0]['id']
    try:
        count = bot.get_chat_members_count(chat_id = channel_id)
        get_chat = bot.get_chat(chat_id = channel_id)
        title = get_chat['title']
        invite_link = get_chat['invite_link']
    except:
        update.message.reply_text(not_found_text)
        return
        
    update.message.reply_text(
        channel_info_text.format(channel_id = channel_id, title = title, count = count, invite_link = invite_link),
        parse_mode = 'Markdown'    
    )

################################################################################## FOOTER

def watch_tower(update, context):

    bot = context.bot
    query = update.callback_query
    data = query.data

    array_data = data.split(' - ')

    if data == 'member?':
        normal_start(query = query, context = context)
    elif data == 'getlink':
        link(query, context)
    elif data == 'answer':
        is_human(query, context)
    elif array_data[0] == 'lang':
        set_lang(query, context, array_data[1])
    else:
        query.answer(carefully_text)

def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater("1140067551:AAGCnp1WENi9PFGGi4GIcRsOXe3vWkuvqnM")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # users
    dispatcher.add_handler(CommandHandler("start", guest, Filters.regex(r"[0-9]")))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("language", wath_is_your_lang))

    # admin
    dispatcher.add_handler(CommandHandler("add", add_channel, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("status", status, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("ban", ban, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("unban", unban, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("top", top, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("user", user, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("send", send, Filters.chat(admin)))
    dispatcher.add_handler(CommandHandler("chan", chan, Filters.chat(admin)))

    # handle callbacks
    updater.dispatcher.add_handler(CallbackQueryHandler(watch_tower))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()