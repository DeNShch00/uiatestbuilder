import sys
import importlib
import traceback
from typing import Iterable

import jsonpickle
import pywinauto
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

import scenario


def save(sc: scenario.Scenario, file_path):
    serialize_str = jsonpickle.encode(sc)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(serialize_str)


def load(file_path) -> scenario.Scenario:
    with open(file_path, encoding='utf-8') as file:
        serialize_str = file.read()

    return jsonpickle.decode(serialize_str)


def build(sc: scenario.Scenario, file_path, debug=False):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(sc.code_gen(debug))


def run_steps(steps: Iterable[scenario.Step]):
    sc = scenario.Scenario()
    sc.steps = steps
    module_file = 'hohohho.py'
    build(sc, module_file, debug=True)
    try:
        module_name = module_file.replace('.py', '')
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)

        module.main()
    except (ElementAmbiguousError, ElementNotFoundError) as exc:
        exc_type = 'ElementAmbiguousError' if isinstance(exc, ElementAmbiguousError) else 'ElementNotFoundError'
        for step in steps:
            for action in step.actions:
                if isinstance(action, scenario.ItemAction):
                    for record in action.item_path.path:
                        if record.id == exc.path_id:
                            return exc_type, (step, action, record)

        assert False
    except:
        return 'OtherError', traceback.format_exc()

    return None, None
