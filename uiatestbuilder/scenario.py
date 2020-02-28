import uiatools
import tools


def _indent(n=1):
    return ' ' * 4 * n


class Action:
    def __init__(self):
        self.id = tools.generate_id()


class ItemAction(Action):
    def __init__(self, item_uia_path: uiatools.ItemPath):
        super().__init__()
        self.item_path = item_uia_path

    def code_gen(self, debug=False):
        code = f'# {self.id}\n'
        code += 'item = desktop\n'
        for record in self.item_path.path[1:]:
            if debug:
                code += f'set_path_id({record.id})\n'

            code += f"item = item.window({record.to_search_str()})\n"

            if debug:
                code += 'item.is_active()\n'

        return code


class ClickAction(ItemAction):
    def __init__(self, item_uia_path: uiatools.ItemPath, mouse_button='left', double_click=False):
        super().__init__(item_uia_path)
        self.mouse_button = mouse_button
        self.double_click = double_click

    def code_gen(self, debug=False):
        code = super().code_gen(debug)
        code += "item.draw_outline(colour='green', thickness=2)\n"
        code += f"item.click_input(button='{self.mouse_button}', double={self.double_click})\n"
        return code


class KeyboardAction(ItemAction):
    def __init__(self, item_uia_path: uiatools.ItemPath, keys: str):
        super().__init__(item_uia_path)
        self.keys = keys

    def code_gen(self, debug=False):
        code = super().code_gen(debug)
        code += f"item.type_keys(keys=r'{self.keys}', pause=1)\n"
        return code


class Step:
    def __init__(self, name):
        self.id = tools.generate_id()
        self.name = name
        self.actions = []

    # def add_action(self, action: Action):
    #     self.actions.append(action)

    def get_func_name(self):
        return f'step_{self.id}'

    def code_gen(self, debug=False):
        code = f'def {self.get_func_name()}():\n'
        code += _indent() + f'"""{self.name}"""\n\n'
        for one in self.actions:
            code += '\n'.join(_indent() + line for line in one.code_gen(debug).splitlines())
            code += '\n\n'

        return code


class Scenario:
    def __init__(self):
        self.steps = []

    # def add_step(self, step: Step):
    #     self.steps.append(step)

    def code_gen(self, debug=False):
        code = 'import pywinauto\n'
        if debug:
            code += 'from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError\n'

        code += '\n\n'
        code += "desktop = pywinauto.Desktop(backend='uia', allow_magic_lookup=False)\n"
        if debug:
            code += 'path_id = 0\n'
            code += '\n\n'
            code += 'def set_path_id(_id):\n' + _indent() + 'global path_id\n' + _indent() + 'path_id = _id\n'

        code += '\n\n'

        for one in self.steps:
            code += one.code_gen(debug)

        code += '\n'
        code += 'def main():\n'

        if debug:
            code += _indent() + 'try:\n'

        for one in self.steps:
            code += _indent(2 if debug else 1) + f'{one.get_func_name()}()\n'

        if debug:
            code += _indent() + 'except (ElementAmbiguousError, ElementNotFoundError) as exc:\n'
            code += _indent(2) + 'exc.path_id = path_id\n'
            code += _indent(2) + 'raise exc\n'


        code += '\n\n'
        code += "if __name__ == '__main__':\n"
        code += _indent() + 'main()\n'

        return code
