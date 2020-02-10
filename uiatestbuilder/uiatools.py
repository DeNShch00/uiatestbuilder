import pywinauto
import pyautogui
import time
import threading

from comtypes import COMError
from pywinauto.base_wrapper import BaseWrapper


class ItemPathRecord:
    def __init__(self, item: BaseWrapper, identical_items_index=None, skip=False):
        self.auto_id = item.element_info.automation_id
        self.title = item.element_info.name
        self.control_type = item.element_info.control_type
        self.control_id = item.element_info.control_id
        self.class_name = item.element_info.class_name
        self.identical_items_index = identical_items_index
        self.skip = skip

    def __repr__(self):
        return str(self.__dict__)


class ItemPath:
    def __init__(self, item: BaseWrapper):
        self.path = []
        while item:
            # TODO: get_identical_items_index() is very slow, must do it faster
            # self.path.append(ItemPathRecord(item, self._get_identical_items_index(item)))
            skip = not item.element_info.name and item.element_info.control_type in ('Pane', 'TitleBar')
            self.path.append(ItemPathRecord(item, skip=skip))
            item = item.parent()

        self.path.reverse()

    @staticmethod
    def _get_identical_items_index(item: BaseWrapper):
        top_item = item.top_level_parent()
        all_items = [top_item, ] + top_item.descendants()
        identical = []
        for one in all_items:
            if one.element_info.name == item.element_info.name:
                if one.element_info.automation_id == item.element_info.automation_id:
                    if one.element_info.control_type == item.element_info.control_type:
                        if one.element_info.control_id == item.element_info.control_id:
                            identical.append(one)

        if len(identical) < 2:
            return None

        for index, one in enumerate(identical):
            if one.rectangle() == item.rectangle():
                return index

        assert False

    def __str__(self):
        res = ''
        for record in self.path:
            if record.title:
                res += f'[{record.title.strip()[:20]}]'
            elif record.control_type:
                res += f'[{record.control_type}]'
            else:
                res += '[]'

        return res


class Scanner:
    def __init__(self):
        self.initial_item = pywinauto.Desktop(backend='uia')
        self.current_path = None
        self.cur_item_rect = None
        self.is_scanning = False
        self.scanning_thread = None

    def start(self):
        if self.scanning_thread:
            self.stop()

        self.is_scanning = True
        self.scanning_thread = threading.Thread(target=self._scan)
        self.scanning_thread.start()

    def stop(self):
        if self.scanning_thread:
            self.is_scanning = False
            self.scanning_thread.join()
            self.scanning_thread = None

    def _item_from_mouse_pos(self):
        for i in range(10):
            x, y = pyautogui.position()
            try:
                return self.initial_item.from_point(x, y)
            except (COMError, KeyError):
                time.sleep(0.1)

    def _is_same_item(self, item):
        rect = item.rectangle()
        same = self.cur_item_rect == rect
        if not same:
            self.cur_item_rect = rect

        return same

    def _scan(self):
        count = 0
        highlight = 'red'
        while self.is_scanning:
            item = self._item_from_mouse_pos()
            if self._is_same_item(item):
                count += 1
            else:
                count = 0
                highlight = 'red'

            if count == 3:
                print('on..', time.process_time())
                self.current_path = ItemPath(item)
                print(self.current_path, time.process_time())
                highlight = 'green'
                count += 1

            item.draw_outline(colour=highlight, thickness=2)
            time.sleep(0.2)

    def get_item_path(self) -> ItemPath:
        # return ItemPath(self._item_from_mouse_pos())
        return self.current_path


def convert_keyboard_keys(hook_keys):

    # key_map = {
    #     'lshift': '{VK_LSHIFT}',
    #     'rshift': '{VK_RSHIFT}',
    #     'lcontrol':'{VK_LCONTROL}',
    #     'rcontrol': '{VK_RCONTROL}',
    #     'lmenu': '{VK_LMENU}',
    #     'rmenu': '{VK_RMENU}',
    #     'back': '{{VK_BACK}',
    #     'return': '{VK_RETURN}',
    #     'tab': '{VK_TAB}',
    # }

    virtual_keys = ('back', 'return', 'tab')
    modifiers = ('lshift', 'rshift', 'lcontrol', 'rcontrol', 'lmenu', 'rmenu')
    additional_keys = ''
    out = ''

    for key in hook_keys:
        key = key.lower()
        if key in modifiers:
            if len(hook_keys) > 1:
                additional_keys += '{VK_%s up}' % key.upper()
                key = '{VK_%s down}' % key.upper()
            else:
                key = '{VK_%s}' % key.upper()

        elif key in virtual_keys:
            key = '{VK_%s}' % key.upper()

        out += key

    return out + additional_keys


def _main():
    sc = Scanner()
    sc.start()
    last_path = ''
    while True:
        path = str(sc.get_item_path())
        if path != last_path:
            print(path)
            last_path = path

        time.sleep(1)


if __name__ == '__main__':
    _main()
