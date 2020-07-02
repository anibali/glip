import enum
import re
from typing import Tuple, Collection, Union, Optional, Set

import glfw

_DIGITS = set('0123456789')


class Key(enum.IntEnum):
    """Enumeration of keyboard keys."""
    SPACE = glfw.KEY_SPACE
    APOSTROPHE = glfw.KEY_APOSTROPHE
    COMMA = glfw.KEY_COMMA
    MINUS = glfw.KEY_MINUS
    PERIOD = glfw.KEY_PERIOD
    SLASH = glfw.KEY_SLASH
    N_0 = glfw.KEY_0
    N_1 = glfw.KEY_1
    N_2 = glfw.KEY_2
    N_3 = glfw.KEY_3
    N_4 = glfw.KEY_4
    N_5 = glfw.KEY_5
    N_6 = glfw.KEY_6
    N_7 = glfw.KEY_7
    N_8 = glfw.KEY_8
    N_9 = glfw.KEY_9
    SEMICOLON = glfw.KEY_SEMICOLON
    EQUAL = glfw.KEY_EQUAL
    A = glfw.KEY_A
    B = glfw.KEY_B
    C = glfw.KEY_C
    D = glfw.KEY_D
    E = glfw.KEY_E
    F = glfw.KEY_F
    G = glfw.KEY_G
    H = glfw.KEY_H
    I = glfw.KEY_I
    J = glfw.KEY_J
    K = glfw.KEY_K
    L = glfw.KEY_L
    M = glfw.KEY_M
    N = glfw.KEY_N
    O = glfw.KEY_O
    P = glfw.KEY_P
    Q = glfw.KEY_Q
    R = glfw.KEY_R
    S = glfw.KEY_S
    T = glfw.KEY_T
    U = glfw.KEY_U
    V = glfw.KEY_V
    W = glfw.KEY_W
    X = glfw.KEY_X
    Y = glfw.KEY_Y
    Z = glfw.KEY_Z
    LEFT_BRACKET = glfw.KEY_LEFT_BRACKET
    BACKSLASH = glfw.KEY_BACKSLASH
    RIGHT_BRACKET = glfw.KEY_RIGHT_BRACKET
    GRAVE_ACCENT = glfw.KEY_GRAVE_ACCENT
    WORLD_1 = glfw.KEY_WORLD_1
    WORLD_2 = glfw.KEY_WORLD_2
    ESCAPE = glfw.KEY_ESCAPE
    ENTER = glfw.KEY_ENTER
    TAB = glfw.KEY_TAB
    BACKSPACE = glfw.KEY_BACKSPACE
    INSERT = glfw.KEY_INSERT
    DELETE = glfw.KEY_DELETE
    RIGHT = glfw.KEY_RIGHT
    LEFT = glfw.KEY_LEFT
    DOWN = glfw.KEY_DOWN
    UP = glfw.KEY_UP
    PAGE_UP = glfw.KEY_PAGE_UP
    PAGE_DOWN = glfw.KEY_PAGE_DOWN
    HOME = glfw.KEY_HOME
    END = glfw.KEY_END
    CAPS_LOCK = glfw.KEY_CAPS_LOCK
    SCROLL_LOCK = glfw.KEY_SCROLL_LOCK
    NUM_LOCK = glfw.KEY_NUM_LOCK
    PRINT_SCREEN = glfw.KEY_PRINT_SCREEN
    PAUSE = glfw.KEY_PAUSE
    F1 = glfw.KEY_F1
    F2 = glfw.KEY_F2
    F3 = glfw.KEY_F3
    F4 = glfw.KEY_F4
    F5 = glfw.KEY_F5
    F6 = glfw.KEY_F6
    F7 = glfw.KEY_F7
    F8 = glfw.KEY_F8
    F9 = glfw.KEY_F9
    F10 = glfw.KEY_F10
    F11 = glfw.KEY_F11
    F12 = glfw.KEY_F12
    F13 = glfw.KEY_F13
    F14 = glfw.KEY_F14
    F15 = glfw.KEY_F15
    F16 = glfw.KEY_F16
    F17 = glfw.KEY_F17
    F18 = glfw.KEY_F18
    F19 = glfw.KEY_F19
    F20 = glfw.KEY_F20
    F21 = glfw.KEY_F21
    F22 = glfw.KEY_F22
    F23 = glfw.KEY_F23
    F24 = glfw.KEY_F24
    F25 = glfw.KEY_F25
    KP_0 = glfw.KEY_KP_0
    KP_1 = glfw.KEY_KP_1
    KP_2 = glfw.KEY_KP_2
    KP_3 = glfw.KEY_KP_3
    KP_4 = glfw.KEY_KP_4
    KP_5 = glfw.KEY_KP_5
    KP_6 = glfw.KEY_KP_6
    KP_7 = glfw.KEY_KP_7
    KP_8 = glfw.KEY_KP_8
    KP_9 = glfw.KEY_KP_9
    KP_DECIMAL = glfw.KEY_KP_DECIMAL
    KP_DIVIDE = glfw.KEY_KP_DIVIDE
    KP_MULTIPLY = glfw.KEY_KP_MULTIPLY
    KP_SUBTRACT = glfw.KEY_KP_SUBTRACT
    KP_ADD = glfw.KEY_KP_ADD
    KP_ENTER = glfw.KEY_KP_ENTER
    KP_EQUAL = glfw.KEY_KP_EQUAL
    LEFT_SHIFT = glfw.KEY_LEFT_SHIFT
    LEFT_CONTROL = glfw.KEY_LEFT_CONTROL
    LEFT_ALT = glfw.KEY_LEFT_ALT
    LEFT_SUPER = glfw.KEY_LEFT_SUPER
    RIGHT_SHIFT = glfw.KEY_RIGHT_SHIFT
    RIGHT_CONTROL = glfw.KEY_RIGHT_CONTROL
    RIGHT_ALT = glfw.KEY_RIGHT_ALT
    RIGHT_SUPER = glfw.KEY_RIGHT_SUPER
    MENU = glfw.KEY_MENU


class ModifierKey(enum.IntEnum):
    """Enumeration of keyboard modifier keys."""
    SHIFT = glfw.MOD_SHIFT
    CONTROL = glfw.MOD_CONTROL
    ALT = glfw.MOD_ALT
    SUPER = glfw.MOD_SUPER
    CAPS_LOCK = glfw.MOD_CAPS_LOCK
    NUM_LOCK = glfw.MOD_NUM_LOCK


KeyLike = Union[Key, int, str]
ModifierKeyLike = Union[ModifierKey, int, str]


def _clean_key(key: KeyLike) -> Key:
    if isinstance(key, Key):
        return key
    if isinstance(key, str):
        if key in _DIGITS:
            return Key[f'N_{key}']
        return Key[key.upper()]
    return Key(key)


def _clean_modifier_key(mod_key: ModifierKeyLike) -> ModifierKey:
    if isinstance(mod_key, ModifierKey):
        return mod_key
    if isinstance(mod_key, str):
        mod_key = mod_key.upper()
        if mod_key == 'CTRL':
            return ModifierKey.CONTROL
        return ModifierKey[mod_key]
    return ModifierKey(mod_key)


class KeyboardShortcut:
    """Description of a keyboard shortcut (a combination of a base key and modifiers)."""
    _parser_regex = re.compile(r'((?:\w+\+)*)(.*)')

    def __init__(self, base_key: KeyLike, modifier_keys: Optional[Collection[ModifierKeyLike]]):
        self.base_key, self.modifier_keys = _clean_key_and_modifiers(base_key, modifier_keys)

    @classmethod
    def parse(cls, string_shortcut: str) -> 'KeyboardShortcut':
        """Create a KeyboardShortcut instance from a string description (eg 'ctrl+s').

        Args:
            string_shortcut: The keyboard shortcut string to parse.

        Returns:
            A corresponding `KeyboardShortcut` instance.
        """
        match = cls._parser_regex.match(string_shortcut)
        if not match or len(match.groups()) != 2:
            raise ValueError(f'malformed shortcut: {string_shortcut}')
        modifiers, base = match.groups()
        if modifiers:
            modifiers = modifiers.lower().split('+')[:-1]
        else:
            modifiers = set()
        return cls(base, modifiers)


def _clean_key_and_modifiers(
    key: Union[KeyLike, KeyboardShortcut],
    mod_keys: Optional[Collection[ModifierKeyLike]]
) -> Tuple[Key, Set[ModifierKey]]:
    if isinstance(key, KeyboardShortcut):
        key, mod_keys = key.base_key, key.modifier_keys
    key = _clean_key(key)
    if mod_keys is not None:
        mod_keys = {_clean_modifier_key(mod_key) for mod_key in mod_keys}
    return key, mod_keys


class Keyboard:
    """An object for tracking keyboard state."""

    def __init__(self):
        self._down_keys = set()
        self._released_keys = set()
        self._pressed_keys = set()
        self._released_buffer = set()
        self._pressed_buffer = set()
        self._modifiers = 0

    def set_key_down(self, key: KeyLike):
        """Fire an event for a key transitioning to the "down" state.

        Args:
            key: The key which transitioned to the "down" state.
        """
        key = _clean_key(key)
        self._pressed_buffer.add(key)
        self._down_keys.add(key)

    def set_key_up(self, key: KeyLike):
        """Fire an event for a key transitioning to the "up" state.

        Args:
            key: The key which transitioned to the "up" state.
        """
        key = _clean_key(key)
        if key in self._down_keys:
            self._released_buffer.add(key)
            self._down_keys.remove(key)

    def set_modifiers(self, mods: int):
        """Set the currently active modifier keys.

        Args:
            mods: The bitmask for modifier keys.
        """
        self._modifiers = mods

    def is_down(self, key: KeyLike, mod_keys: Optional[Collection[ModifierKeyLike]] = None) -> bool:
        """Check whether a key is down.

        Args:
            key: The key to check.
            mod_keys: An optional collection of modifier keys which must be active.

        Returns:
            `True` if the key is down, `False` otherwise.
        """
        key, mod_keys = _clean_key_and_modifiers(key, mod_keys)
        return key in self._down_keys and self.has_exact_modifiers(mod_keys)

    def is_up(self, key: KeyLike, mod_keys: Optional[Collection[ModifierKeyLike]] = None) -> bool:
        """Check whether a key is up.

        Args:
            key: The key to check.
            mod_keys: An optional collection of modifier keys which must be active.

        Returns:
            `True` if the key is up, `False` otherwise.
        """
        return not self.is_down(key, mod_keys)

    def was_released(self, key: KeyLike, mod_keys: Optional[Collection[ModifierKeyLike]] = None) -> bool:
        """Check whether a key was just released (down -> up transition).

        Args:
            key: The key to check.
            mod_keys: An optional collection of modifier keys which must be active.

        Returns:
            `True` if the key was just released, `False` otherwise.
        """
        key, mod_keys = _clean_key_and_modifiers(key, mod_keys)
        return key in self._released_keys and self.has_exact_modifiers(mod_keys)

    def was_pressed(self, key: KeyLike, mod_keys: Optional[Collection[ModifierKeyLike]] = None) -> bool:
        """Check whether a key was just pressed (up -> down transition).

        Args:
            key: The key to check.
            mod_keys: An optional collection of modifier keys which must be active.

        Returns:
            `True` if the key was just pressed, `False` otherwise.
        """
        key, mod_keys = _clean_key_and_modifiers(key, mod_keys)
        return key in self._pressed_keys and self.has_exact_modifiers(mod_keys)

    def has_modifier(self, mod_key: ModifierKeyLike) -> bool:
        """Check whether a modifier key is active.

        Args:
            mod_key: The modifier key to check.

        Returns:
            `True` if the modifier key is active, `False` otherwise.
        """
        mod_key = _clean_modifier_key(mod_key)
        return (self._modifiers & mod_key.value) != 0

    def has_exact_modifiers(self, mod_keys: Optional[Collection[ModifierKeyLike]]) -> bool:
        """Check whether a collection of modifier keys are active.

        Args:
            mod_keys: The modifier keys to check.

        Returns:
            `True` if `mod_keys` is `None` or the specified modifier keys are the only ones active,
            `False` otherwise.
        """
        if mod_keys is None:
            return True
        cur_modifiers = 0
        for mod_key in mod_keys:
            cur_modifiers |= mod_key.value
        mask = ModifierKey.ALT.value | ModifierKey.CONTROL.value | ModifierKey.SHIFT.value | ModifierKey.SUPER.value
        return self._modifiers & mask == cur_modifiers & mask

    def update(self):
        """Update the keyboard state, enabling the detection of key state transitions.
        """
        if len(self._released_buffer) > 0:
            self._released_keys = self._released_buffer
            self._released_buffer = set()
        elif len(self._released_keys) > 0:
            self._released_keys = set()
        if len(self._pressed_buffer) > 0:
            self._pressed_keys = self._pressed_buffer
            self._pressed_buffer = set()
        elif len(self._pressed_keys) > 0:
            self._pressed_keys = set()
