import queue

import tkinter
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

import scenario
import recorder
import scenariotools
import uiatools


class Application:
    def __init__(self):
        self.sc = scenario.Scenario()
        self.rec = recorder. Recorder()
        self.is_recording = False
        self.current_step = None
        self.step_counter = 1
        self.action_list_current_insert_index = None
        self.active_on_stop_group = []

        self.main_wnd = tkinter.Tk()
        self.main_wnd.title('Pywinauto test generator')

        box = tkinter.Frame(self.main_wnd)
        box.pack(fill=tkinter.BOTH, expand=1)

        frame = tkinter.Frame(box)
        frame.pack(fill=tkinter.X, expand=1)
        scrollbar = tkinter.Scrollbar(frame)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.action_list = tkinter.Listbox(frame, selectmode=tkinter.SINGLE, yscrollcommand=scrollbar.set)
        self.action_list.pack(fill=tkinter.X, expand=1)
        scrollbar.config(command=self.action_list.yview)

        self.record_btn = tkinter.Button(box, text='Start', command=self.on_start_record)
        self.record_btn.pack()
        btn = tkinter.Button(box, text='New', command=self.on_new_scenario)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Add Step...',  command=self.on_add_step)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Delete', command=self.on_del_action)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Run', command=self.on_run_step)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Load...', command=self.on_load_scenario)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Save...', command=self.on_save_scenario)
        btn.pack()
        self.active_on_stop_group.append(btn)
        btn = tkinter.Button(box, text='Tune...', command=self.on_tune_item_path)
        btn.pack()
        self.active_on_stop_group.append(btn)

        frame = tkinter.Frame(box)
        frame.pack(fill=tkinter.X, expand=1)
        scrollbar = tkinter.Scrollbar(frame)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.status_area = tkinter.Text(frame, wrap=tkinter.WORD, yscrollcommand=scrollbar.set)
        self.status_area.pack(fill=tkinter.X, expand=1)
        scrollbar.config(command=self.status_area.yview)

    def add_status(self, text):
        self.status_area.insert(tkinter.END, text + '\n')
        self.status_area.see(tkinter.END)

    def new_scenario_set(self):
        self.action_list.delete(0, tkinter.END)
        self.status_area.delete(1.0, tkinter.END)
        self.step_counter = 1

    def on_new_scenario(self):
        self.sc = scenario.Scenario()
        self.new_scenario_set()

    def on_load_scenario(self):
        path = askopenfilename(filetypes=(("Scenario files", "*.uiasc"),))
        if not path:
            return

        self.sc = scenariotools.load(path)
        self.new_scenario_set()

        for step in self.sc.steps:
            self.action_list_add_step(step)
            self.step_counter += 1
            for action in step.actions:
                self.action_list_add_action(tkinter.END, action)

        self.add_status('Loaded: ' + path)

    def on_save_scenario(self):
        path = asksaveasfilename(defaultextension=".uiasc")
        if path:
            scenariotools.save(self.sc, path)
            self.add_status('Saved: ' + path)

    def on_run_step(self):
        index, step, action = self.get_selected_step_action()
        if step and not action:
            self.add_status('Run step: ' + step.name)
            exception = scenariotools.run_steps((step,))
            self.add_status(exception)
        else:
            self.add_status('No step selected')

    def set_current_step(self):
        self.current_step = None
        index, step, action = self.get_selected_step_action()
        if step and not action:
            self.current_step = step
        elif len(self.sc.steps):
            self.current_step = self.sc.steps[-1]

        if not self.current_step:
            return False

        index = 0
        for step in self.sc.steps:
            index += len(step.actions) + 1
            if step == self.current_step:
                self.action_list_current_insert_index = index
                break

        return True

    def on_start_record(self):
        if self.is_recording:
            self.is_recording = False
            self.rec.stop()
            self.record_btn['text'] = 'Start'
            for one in self.active_on_stop_group:
                one['state'] = tkinter.NORMAL
        else:
            if self.set_current_step():
                self.is_recording = True
                self.rec.start()
                self.get_action_loop()
                self.record_btn['text'] = 'Stop'
                for one in self.active_on_stop_group:
                    one['state'] = tkinter.DISABLED

                self.add_status('Start record step: ' + self.current_step.name)
            else:
                self.add_status('No step selected')

    def on_add_step(self):
        dlg = StepNameDlg(self.step_counter)
        if dlg.show() == 'OK':
            step = scenario.Step(dlg.step_name)
            self.sc.steps.append(step)
            self.action_list_add_step(step)
            self.step_counter += 1

    def on_tune_item_path(self):
        index, step, action = self.get_selected_step_action()
        if action and  isinstance(action, scenario.ItemAction):
            TuneItemPathDlg(action.item_path).show()
        else:
            self.add_status('No action on item selected')

    def action_list_add_step(self, step):
        self.action_list.insert(tkinter.END, step.name)
        self.action_list.see(tkinter.END)

    def on_add_action(self, action):
        self.current_step.actions.append(action)
        self.action_list_add_action(self.action_list_current_insert_index, action)
        self.action_list_current_insert_index += 1

    def action_list_add_action(self, index, action):
        if isinstance(action, scenario.ClickAction):
            text = f"click {action.mouse_button}{' double' if action.double_click else ''} "
            text += str(action.item_path)
        elif isinstance(action, scenario.KeyboardAction):
            text = f'keyboard "{action.keys}" {str(action.item_path)}'
        else:
            text = 'unknown action ' + str(type(action))

        text = '    ' + text
        self.action_list.insert(index, text)
        self.action_list.see(index)

    def get_action_loop(self):
        if self.is_recording:
            self.add_status(str(self.rec.get_current_item_path()))

            try:
                action = self.rec.action_queue.get_nowait()
            except queue.Empty:
                action = None

            if action:
                self.on_add_action(action)

            self.main_wnd.after(1000, self.get_action_loop)

    def on_del_action(self):
        index, step, action = self.get_selected_step_action()
        if index is None:
            self.add_status('No step or action selected')
            return

        msg = 'Are sure you want to delete item ?'
        result = tkinter.messagebox.askquestion('', msg, icon='warning', default=tkinter.messagebox.NO)
        if result != 'yes':
            return

        if action:
            self.action_list.delete(index)
            step.actions.remove(action)
        else:
            self.action_list.delete(index, index + len(step.actions))
            self.sc.steps.remove(step)

        self.action_list.selection_clear(0, tkinter.END)

    def get_selected_step_action(self):
        index = self.action_list.curselection()
        if len(index) == 0:
            return None, None, None

        index = int(index[0])
        count = 0
        for step in self.sc.steps:
            if index == count:
                return index, step, None
            else:
                n = len(step.actions)
                if index <= count + n:
                    for action in step.actions:
                        count += 1
                        if index == count:
                            return index, step, action
                else:
                    count += n + 1

        assert False

    def run(self):
        self.main_wnd.mainloop()


class ModalDialog:
    def __init__(self):
        self.dialog = tkinter.Toplevel()
        self.result = None

    def show(self):
        self.dialog.focus_set()
        self.dialog.grab_set()
        self.dialog.wait_window()
        return self.result


class OkCancelModalDialog(ModalDialog):
    def __init__(self, ):
        super().__init__()
        self.body_frame = tkinter.Frame(self.dialog)
        self.body_frame.pack(fill=tkinter.BOTH, expand=1)
        self.footer_frame = tkinter.Frame(self.dialog)
        self.footer_frame.pack(fill=tkinter.Y, expand=1)
        self.ok_btn = tkinter.Button(self.footer_frame, text='OK', command=self.on_ok)
        self.ok_btn.pack()
        self.cancel_btn = tkinter.Button(self.footer_frame, text='Cancel', command=self.on_cancel)
        self.cancel_btn.pack()
        self.result = 'Cancel'

    def on_ok(self):
        self.result = 'OK'
        self.dialog.destroy()

    def on_cancel(self):
        self.result = 'Cancel'
        self.dialog.destroy()


class StepNameDlg(OkCancelModalDialog):
    def __init__(self, step_counter):
        super().__init__()
        self.step_name = f'Step {step_counter}'
        self.name_entry = tkinter.Entry(self.body_frame)
        self.name_entry.pack(fill=tkinter.X, expand=1)
        self.name_entry.insert(0, self.step_name)
        self.name_entry.bind('<FocusIn>', self.on_name_enty_focus)

    def on_name_enty_focus(self, event):
        self.name_entry.selection_range(0, tkinter.END)

    def on_ok(self):
        if not self.name_entry.get():
            return

        self.step_name = self.name_entry.get()
        super().on_ok()


class TuneItemPathDlg(OkCancelModalDialog):
    def __init__(self, path: uiatools.ItemPath):
        super().__init__()
        self.path = path
        self.text_ateas = []
        for record in path.path:
            box = tkinter.Frame(self.body_frame)
            box.pack(fill=tkinter.X, expand=1)
            tkinter.Label(box, text=f'[{record.friendly_name()}]').pack()
            scrollbar = tkinter.Scrollbar(box)
            scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
            area = tkinter.Text(box, height=5, wrap=tkinter.WORD, yscrollcommand=scrollbar.set)
            area.pack(fill=tkinter.X, expand=1)
            scrollbar.config(command=area.yview)
            area.insert(0.0, record.to_enum_str())
            self.text_ateas.append(area)

        tkinter.Label(self.body_frame, text='Remove "-" to enable path property.').pack()

    def on_ok(self):
        try:
            for i, record in enumerate(self.path.path):
                record.from_enum_str(self.text_ateas[i].get(0.0, tkinter.END))
        except uiatools.ItemPathRecord.InvalidEnumStr as exc:
            tkinter.messagebox.showerror(message=str(exc))
            return

        super().on_ok()
