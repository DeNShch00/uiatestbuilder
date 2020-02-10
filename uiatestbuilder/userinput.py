import time
import threading
from pywinauto.win32_hooks import Hook
from pywinauto.win32_hooks import KeyboardEvent
from pywinauto.win32_hooks import MouseEvent
from typing import Callable, List, Any


class MouseInputHandler:
    def __init__(self, click_handler: Callable[[str, bool, Any], None], click_context_builder: Callable):
        self.click_handler = click_handler
        self.get_click_context = click_context_builder
        self.click_context = None

        self.was_left_double_click = False
        self.was_left_single_click = False
        self.left_click_thread = None
        self.left_click_lock = threading.Lock()

    def _left_single_click(self):
        time.sleep(0.3)
        with self.left_click_lock:
            if not self.was_left_double_click:
                self.was_left_single_click = True
                self.click_handler('left', False, self.click_context)

    def on_left_click(self):
        new_click = True

        if self.left_click_thread:
            with self.left_click_lock:
                if not self.was_left_single_click:
                    self.was_left_double_click = True
                    self.click_handler('left', True, self.click_context)
                    new_click = False
            self.left_click_thread.join()
            self.left_click_thread = None

        if new_click:
            self.click_context = self.get_click_context()
            self.was_left_double_click = False
            self.was_left_single_click = False
            self.left_click_thread = threading.Thread(target=self._left_single_click)
            self.left_click_thread.start()

    def on_right_click(self):
        self.click_handler('right', False, self.get_click_context())


class KeyboardInputHandler:
    def __init__(self, key_press_handler: Callable[[List[str]], None]):
        self.key_press_handler = key_press_handler

    def on_key_press(self, pressed_key):
        self.key_press_handler(pressed_key)


class UserInput:
    def __init__(self, mouse_input_handler: MouseInputHandler, keyboard_input_handler: KeyboardInputHandler):
        self.mouse_input_handler = mouse_input_handler
        self.keyboard_input_handler = keyboard_input_handler
        self.hook = Hook()
        self.hook.handler = self._on_keyboard_mouse_event
        self.thread = None

    def start(self):
        if self.thread:
            self.stop()

        self.thread = threading.Thread(target=self._hooking_input)
        self.thread.start()

    def stop(self):
        if self.thread:
            self.hook.stop()
            self.thread.join()
            self.thread = None

    def _hooking_input(self):
        self.hook.hook(keyboard=True, mouse=True)

    def _on_keyboard_mouse_event(self, event):
        if isinstance(event, MouseEvent):
            # print(event.event_type, event.current_key)
            if event.event_type == 'key down':
                if event.current_key == 'LButton':
                    self.mouse_input_handler.on_left_click()
                elif event.current_key == 'RButton':
                    self.mouse_input_handler.on_right_click()
        elif isinstance(event, KeyboardEvent):
            # print(event.pressed_key)
            self.keyboard_input_handler.on_key_press(event.pressed_key)


def _main():
    mih = MouseInputHandler(lambda btn, dbl, ctx: print(f'button={btn}, double_click={dbl}, context={ctx}'),
                            time.process_time)
    kih = KeyboardInputHandler(lambda key: print('press', key))
    ui = UserInput(mih, kih)
    ui.start()
    while True:
        pass


if __name__ == '__main__':
    _main()
