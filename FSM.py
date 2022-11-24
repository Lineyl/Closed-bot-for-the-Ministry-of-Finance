from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

storage = MemoryStorage()
class findemployee(StatesGroup):
    textfind = State()
    numemp = State()

class SendOffer(StatesGroup):
    waitOffer = State()

class contactModer(StatesGroup):
    waitMessage = State()
    moder_to_user = State()
    user_to_moder = State()

class AdminSendFileDB(StatesGroup):
    waitCommand = State()
    waitFileExel = State()
    waitToRemove = State()
    removeByID = State()
    removeBySurname = State()
    waitID = State()