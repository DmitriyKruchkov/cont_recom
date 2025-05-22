import os
import sys
from config import api_id, api_hash
from telethon.sync import TelegramClient
from telethon.sessions import StringSession



def get_value(of_what: str):
    val = os.getenv(of_what)
    if not val:
        val = input(f'Enter the value of {of_what}:\n>')
        if not val:
            print('Recieved no input. Quitting.')
            sys.exit()
        return val
    return val


print('\nYou are now going to login, and the session string will be displayed on screen. \nYou need to copy that for future use.')

input('\nPress [ENTER] to proceed \n?')

phone = input('Enter you phone number in international format: ')

if not phone:
    print('You did not enter your phone number. Quitting.')
    sys.exit()

with TelegramClient(StringSession(), api_id, api_hash).start(phone=phone) as client:
    print('\n\nBelow is your session string ⬇️\n\n')
    print(client.session.save())
    print('\nAbove is your session string ⬆️\n\n')
