from aiogram.fsm.state import State, StatesGroup


class YogaState(StatesGroup):
    waiting_for_time = State()


class PlankState(StatesGroup):
    choosing_sets = State()
    adjusting = State()
