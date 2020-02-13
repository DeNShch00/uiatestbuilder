import pywinauto
import pyautogui
import time
import threading

from comtypes import COMError
from pywinauto.base_wrapper import BaseWrapper
from typing import Optional


class ItemPathRecord:
    class InvalidString(Exception):
        pass

    def __init__(self, item: BaseWrapper, identical_items_index=None):
        self.props = {
            '-class_name': item.element_info.class_name,
            '-class_name_re': None,
            '-process': item.element_info.process_id,
            'title': item.element_info.name,
            '-title_re': None,
            '-top_level_only': True,
            '-visible_only': item.element_info.visible,
            '-enabled_only': item.element_info.enabled,
            '-best_match': None,
            '-handle': item.element_info.handle,
            '-ctrl_index': None,
            '-found_index': identical_items_index,
            '-active_only': False,
            'control_id': item.element_info.control_id,
            'control_type': item.element_info.control_type,
            'auto_id': item.element_info.automation_id,
            '-framework_id': item.element_info.framework_id,
            '-backend': None,
            '-depth': None
        }

        # t = time.process_time()
        # self.auto_id = item.element_info.automation_id
        # self.title = item.element_info.name
        # self.control_type = item.element_info.control_type
        # self.control_id = item.element_info.control_id
        # self.class_name = item.element_info.class_name
        # self.identical_items_index = identical_items_index
        # print(item.element_info.handle)
        # print(item.element_info.framework_id)
        # print(item.element_info.rich_text)
        # print(item.element_info.runtime_id)
        # print('t1 ', time.process_time() - t, end=' ')
        # # t = item.element_info.element
        # # print(t)
        # # print(type(t))
        # # print(t.__dict__)
        # # print(item.get_properties())
        # # print(item.writable_props)
        #
        # t = time.process_time()
        # self.p = item.get_properties()
        # print('t2 ', time.process_time() - t)
        #
        # # y = pywinauto.Desktop(backend='uia')
        # # y = y.window(title='ff')
        # # y.print_control_identifiers()

    def __getitem__(self, key):
        return self.props.get(key, self.props['-' + key])

    def to_str(self):
        return str(self.props)

    def from_str(self, string):
        try:
            self.props = eval('{' + string + '}')
        except Exception:
            raise self.InvalidString

    def to_search_str(self, include_empty_props=False):
        pairs = []
        for key, value in self.props.items():
            if not key.startswith('-'):
                if not include_empty_props and (value is None or value == ''):
                    continue

                prefix, postfix = ("r'", "'") if isinstance(value, str) else ('', '')
                pairs.append(f'{key}={prefix}{value}{postfix}')

        return ', '.join(pairs)


    # def __repr__(self):
    #     return str(self.__dict__)


class ItemPath:
    def __init__(self, item: Optional[BaseWrapper] = None):
        self.path = []
        while item:
            # TODO: get_identical_items_index() is very slow, must do it faster
            # self.path.append(ItemPathRecord(item, self._get_identical_items_index(item)))
            self.path.append(ItemPathRecord(item))
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
            title = record['title']
            type = record['control_type']
            if title:
                res += f'[{title[:20]}]'
            elif type:
                res += f'[{type}]'
            else:
                res += '[]'

        return res


class Scanner:
    def __init__(self):
        self.initial_item = pywinauto.Desktop(backend='uia')
        self.current_path = ItemPath()
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
            self.scanning_thread.join(timeout=5)
            self.scanning_thread = None

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
            try:
                item = self.initial_item.from_point(*pyautogui.position())
                if self._is_same_item(item):
                    count += 1
                else:
                    count = 0
                    highlight = 'red'

                if count == 3:
                    self.current_path = ItemPath(item)
                    highlight = 'green'
                    count += 1

                item.draw_outline(colour=highlight, thickness=2)
            except (COMError, KeyError):
                self.current_path = ItemPath()

            time.sleep(0.2)

    def get_item_path(self) -> ItemPath:
        return self.current_path


def kb_keys_hook_to_uia(hook_keys):
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
