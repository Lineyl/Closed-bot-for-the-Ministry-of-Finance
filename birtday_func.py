import datetime
import asyncio
from time import sleep

from main import bot
from sqldb import cur

async def birtday_func():
    date = datetime.datetime.now().strftime('%d.%m')
    time = datetime.datetime.now().strftime('%H:%M')
    list_birthday = cur.execute("SELECT * FROM employee").fetchall()
    b = []
    t = False
    for d in list_birthday:
        if date in d[6]:
            b.append(d)
            t = True
    if time == "14:23" and t:
        await bot.send_message(438202772, f"{b}")
        sleep(61)
loop = asyncio.get_event_loop()
loop.run_forever()
