import queue

import scenario
import uiatools
import userinput


class Recorder:
    def __init__(self):
        self.scanner = uiatools.Scanner()

        mih = userinput.MouseInputHandler(self._on_mouse_click, self.scanner.get_item_path)
        kih = userinput.KeyboardInputHandler(self._on_key_press)
        self.input = userinput.UserInput(mih, kih)

        self.action_queue = queue.Queue()
        self.keyboard_buffer = ''
        self.keyboard_item = None
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.action_queue = queue.Queue()
            self.scanner.start()
            self.input.start()
            self.is_running = True

    def stop(self):
        if self.is_running:
            self.input.stop()
            self.scanner.stop()
            self.is_running = False

    def _on_mouse_click(self, button, double, item_path):
        self.action_queue.put(scenario.ClickAction(item_path, button, double))

    def _on_key_press(self, keys):
        if keys == ['Rcontrol']:
            if self.keyboard_buffer:
                self.action_queue.put(scenario.KeyboardAction(self.keyboard_item, self.keyboard_buffer))
                self.keyboard_buffer = ''
            else:
                self.keyboard_item = self.scanner.get_item_path()
        else:
            self.keyboard_buffer += uiatools.kb_keys_hook_to_uia(keys)

    def get_current_item_path(self):
        return self.scanner.get_item_path()
