import random

import uiatools



def _generate_id():
    return random.randint(1, 10**10)


def _indent(n=1):
    return ' ' * 4 * n


class Action:
    def __init__(self):
        self.id = _generate_id()


class ItemAction(Action):
    def __init__(self, item_uia_path: uiatools.ItemPath):
        super().__init__()
        self.item_path = item_uia_path

    def code_gen(self):
        code = f'# {self.id}\n'
        code += 'item = desktop\n'
        for record in self.item_path.path[1:]:
            code += f"{'# ' if record.skip else ''}item = item.window(" \
                f"auto_id=r'{record.auto_id}', " \
                f"title=r'{record.title}', " \
                f"control_type='{record.control_type}', " \
                f"control_id={record.control_id}, " \
                f"found_index={record.identical_items_index})\n"

        return code


class ClickAction(ItemAction):
    def __init__(self, item_uia_path: uiatools.ItemPath, mouse_button='left', double_click=False):
        super().__init__(item_uia_path)
        self.mouse_button = mouse_button
        self.double_click = double_click

    def code_gen(self):
        code = super().code_gen()
        code += "item.draw_outline(colour='green', thickness=2)\n"
        code += f"item.click_input(button='{self.mouse_button}', double={self.double_click})\n"
        return code


class KeyboardAction(ItemAction):
    def __init__(self, item_uia_path: uiatools.ItemPath, keys: str):
        super().__init__(item_uia_path)
        self.keys = keys

    def code_gen(self):
        code = super().code_gen()
        code += f"item.type_keys(keys=r'{self.keys}')\n"
        return code


class Step:
    def __init__(self, name):
        self.id = _generate_id()
        self.name = name
        self.actions = []

    # def add_action(self, action: Action):
    #     self.actions.append(action)

    def get_func_name(self):
        return f'step_{self.id}'

    def code_gen(self):
        code = f'def {self.get_func_name()}():\n'
        code += _indent() + f'"""{self.name}"""\n\n'
        for one in self.actions:
            code += '\n'.join(_indent() + line for line in one.code_gen().splitlines())
            code += '\n\n'

        return code


class Scenario:
    def __init__(self):
        self.steps = []

    # def add_step(self, step: Step):
    #     self.steps.append(step)

    def code_gen(self):
        code = 'import pywinauto\n\n\n'
        code += "desktop = pywinauto.Desktop(backend='uia', allow_magic_lookup=False)\n\n\n"
        for one in self.steps:
            code += one.code_gen()

        code += '\n\n'
        code += 'def main():\n'
        for one in self.steps:
            code += _indent() + f'{one.get_func_name()}()\n'

        code += '\n\n'
        code += "if __name__ == '__main__':\n"
        code += _indent() + 'main()\n'

        return code
