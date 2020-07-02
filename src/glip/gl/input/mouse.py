import enum

import glfw


class MouseButton(enum.Enum):
    """Enumeration of mouse buttons."""
    LEFT = glfw.MOUSE_BUTTON_LEFT
    MIDDLE = glfw.MOUSE_BUTTON_MIDDLE
    RIGHT = glfw.MOUSE_BUTTON_RIGHT


class Mouse:
    """An object for tracking mouse state."""

    def __init__(self):
        self._down_buttons = set()
        self._released_buttons = set()
        self._pressed_buttons = set()
        self._released_buffer = set()
        self._pressed_buffer = set()
        self.x = 0
        self.y = 0
        self.down_x = 0
        self.down_y = 0

    def fire_button_down(self, button, x, y):
        self._pressed_buffer.add(button)
        self._down_buttons.add(button)
        self.down_x = x
        self.down_y = y

    def fire_button_up(self, button, x, y):
        if button in self._down_buttons:
            self._released_buffer.add(button)
            self._down_buttons.remove(button)

    def fire_move(self, x, y):
        self.x = x
        self.y = y

    def _clean_button(self, button):
        if isinstance(button, MouseButton):
            return button.value
        return button

    def is_down(self, button):
        return self._clean_button(button) in self._down_buttons

    def is_up(self, button):
        return not self.is_down(button)

    def was_released(self, button):
        return self._clean_button(button) in self._released_buttons

    def was_pressed(self, button):
        return self._clean_button(button) in self._pressed_buttons

    def update(self):
        if len(self._released_buffer) > 0:
            self._released_buttons = self._released_buffer
            self._released_buffer = set()
        elif len(self._released_buttons) > 0:
            self._released_buttons = set()
        if len(self._pressed_buffer) > 0:
            self._pressed_buttons = self._pressed_buffer
            self._pressed_buffer = set()
        elif len(self._pressed_buttons) > 0:
            self._pressed_buttons = set()
