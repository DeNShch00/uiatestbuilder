import subprocess
from typing import Iterable

import jsonpickle

import scenario


def save(sc: scenario.Scenario, file_path):
    serialize_str = jsonpickle.encode(sc)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(serialize_str)


def load(file_path) -> scenario.Scenario:
    with open(file_path, encoding='utf-8') as file:
        serialize_str = file.read()

    return jsonpickle.decode(serialize_str)


def build(sc: scenario.Scenario, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(sc.code_gen())


def run_steps(steps: Iterable[scenario.Step]):
    sc = scenario.Scenario()
    sc.steps = steps
    file = 'hohohho.py'
    interpreter = r'C:\Program Files\Python37\python.exe'
    build(sc, file)
    return _run_cmd(interpreter + ' ' + file)


def _run_cmd(cmd):
    process = subprocess.Popen(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

