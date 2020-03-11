import uiatools
import tools


def _indent(n=1):
    return ' ' * 4 * n


class Globals:
    imports = []
    variables = []
    functions = []
    exception_handlers = []

    @staticmethod
    def _append_unique(list_, value):
        if value not in list_:
            list_.append(value)

    @staticmethod
    def add_import(code):
        Globals._append_unique(Globals.imports, code)

    @staticmethod
    def add_variable(code):
        Globals._append_unique(Globals.variables, code)

    @staticmethod
    def add_function(code):
        Globals._append_unique(Globals.functions, code)

    @staticmethod
    def add_exception_handler(code):
        Globals._append_unique(Globals.exception_handlers, code)


class Action:
    def __init__(self):
        self.id = tools.generate_id()

    def globals_gen(self, debug=False):
        raise RuntimeError('not implemented')

    def code_gen(self, debug=False):
        raise RuntimeError('not implemented')


class ItemAction(Action):
    def __init__(self, item_uia_path: uiatools.ItemPath):
        super().__init__()
        self.item_path = item_uia_path

    def globals_gen(self, debug=False):
        Globals.add_import('import pywinauto\n')
        Globals.add_variable("desktop = pywinauto.Desktop(backend='uia', allow_magic_lookup=False)\n")

        if debug:
            Globals.add_import('from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError\n')
            Globals.add_variable('path_id = 0\n')

            code = 'def set_path_id(_id):\n' + _indent() + 'global path_id\n' + _indent() + 'path_id = _id\n'
            Globals.add_function(code)

            code = 'except (ElementAmbiguousError, ElementNotFoundError) as exc:\n'
            code += _indent() + 'exc.path_id = path_id\n'
            code += _indent() + 'raise exc\n'
            Globals.add_exception_handler(code)

    def code_gen(self, debug=False):
        code = 'item = desktop\n'
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


class SleepAction(Action):
    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds

    def globals_gen(self, debug=False):
        Globals.add_import('import time')

    def code_gen(self, debug=False):
        return f'time.sleep({self.seconds})\n'


class SignalAction(Action):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    def globals_gen(self, debug=False):
        Globals.add_import('import socket')


class WaitForSignalAction(SignalAction):
    def __init__(self, port):
        super().__init__(0, port)

    def code_gen(self, debug=False):
        code = 'serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n'
        code += f'serversocket.bind((socket.gethostname(), {self.port}))\n'
        code += 'serversocket.listen(5)\n'
        code += '(clientsocket, address) = serversocket.accept()\n'
        code += 'clientsocket.recv(1024)\n'
        code += 'clientsocket.shutdown(socket.SHUT_RDWR)\n'
        code += 'clientsocket.close()\n'
        code += 'serversocket.close()\n'
        return code


class SendSignalAction(SignalAction):
    def __init__(self, host, port):
        super().__init__(host, port)

    def code_gen(self, debug=False):
        code = 'clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n'
        code += f'clientsocket.connect(({self.host}, {self.port}))\n'
        code += 'clientsocket.send("0")\n'
        code += 'clientsocket.shutdown(socket.SHUT_RDWR)\n'
        code += 'clientsocket.close()\n'
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

    def globals_gen(self, debug=False):
        for one in self.actions:
            one.globals_gen(debug)

    def code_gen(self, debug=False):
        code = f'def {self.get_func_name()}():\n'
        code += _indent() + f'""" {self.name} """\n\n'
        last = len(self.actions) - 1
        for num, one in enumerate(self.actions):
            code += _indent() + f'# {one.__class__.__name__} {one.id}\n'
            code += ''.join(_indent() + line + '\n' for line in one.code_gen(debug).splitlines())
            if num != last:
                code += '\n'

        return code


class Scenario:
    def __init__(self):
        self.steps = []

    # def add_step(self, step: Step):
    #     self.steps.append(step)

    def code_gen(self, debug=False):
        code = '""" Code generated by uiatestbuilder """\n\n'
        for one in self.steps:
            one.globals_gen(debug)

        code += ''.join(Globals.imports)
        code += '\n\n' if len(Globals.imports) else ''
        code += ''.join(Globals.variables)
        code += '\n\n' if len(Globals.variables) else ''
        code += '\n\n'.join(Globals.functions)
        code += '\n\n' if len(Globals.functions) else ''
        code += '\n\n'.join((one.code_gen(debug) for one in self.steps))
        code += '\n\n'

        code += 'def main():\n'
        try_block = len(Globals.exception_handlers) > 0
        if try_block :
            code += _indent() + 'try:\n'

        for one in self.steps:
            code += _indent(2 if try_block else 1) + f'{one.get_func_name()}()\n'

        code += ''.join((_indent() + line + '\n' for one in Globals.exception_handlers for line in one.splitlines()))

        code += '\n\n'
        code += "if __name__ == '__main__':\n"
        code += _indent() + 'main()\n'

        return code
