import time
import threading

import pywinauto
import pyautogui

from comtypes import COMError
from pywinauto.base_wrapper import BaseWrapper
from typing import Optional

import tools


class ItemPathRecord:
    class InvalidEnumStr(Exception):
        pass

    def __init__(self, item: BaseWrapper, identical_items_index=None):
        self.id = tools.generate_id()
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

    def __getitem__(self, key):
        try:
            return self.props[key]
        except KeyError:
            pass

        return self.props['-' + key]

    def to_enum_str(self):
        return '\n'.join([f'{k}={v}' for k, v in self._items(False, True, True)])

    def to_search_str(self, include_empty_props=False):
        return ', '.join([f'{k}={v}' for k, v in self._items(True, False, include_empty_props)])

    def _items(self, raw_str: bool, include_disabled: bool, include_empty: bool):
        for key, value in self.props.items():
            if include_disabled or not key.startswith('-'):
                if include_empty or (value is not None and value != ''):
                    if isinstance(value, str):
                        yield key, '{}"{}"'.format('r' if raw_str else '', value)
                    else:
                        yield key, str(value)

    def from_enum_str(self, enum):
        props = {}
        for line in enum.splitlines():
            pair = line.split('=', 1)
            if len(pair) != 2:
                raise self.InvalidEnumStr(f'[{self.friendly_name()}], invalid record: [{line}]')

            key, value = pair
            key = key.strip()
            value = value.strip()

            disabled = key.startswith('-')
            origin_key = key.strip('-')  # for case: '---key'
            try:
                self[origin_key]
            except KeyError:
                raise self.InvalidEnumStr(f'[{self.friendly_name()}], invalid key: [{key}]')

            key = origin_key if not disabled else '-' + origin_key
            try:
                if value == 'None':
                    props[key] = None
                elif value == 'False':
                    props[key] = False
                elif value == 'True':
                    props[key] = True
                elif value[0].isdigit():
                    props[key] = int(value)
                else:
                    props[key] = value.strip('"')
            except (IndexError, ValueError):
                raise self.InvalidEnumStr(f'[{self.friendly_name()}], invalid value: [{value}] for key [{key}]')

        self.props = props

    def friendly_name(self):
        title = self['title']
        type = self['control_type']
        return title[:20] if title else type


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
        return ''.join([f'[{x.friendly_name()}]' for x in self.path])


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
