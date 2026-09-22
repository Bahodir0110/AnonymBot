"""Finite State Machine (FSM) states for student interactions."""

from aiogram.fsm.state import State, StatesGroup


class AppealStates(StatesGroup):
    """States for the appeal submission flow."""
    waiting_for_appeal = State()
