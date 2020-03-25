import os
from gi.repository import Gtk, Gdk


class FileChooser(object):

    def __init__(self, type):
        self.builder = Gtk.Builder()
        current_path = os.path.dirname(__file__)
        path = os.path.join(current_path, "file_chooser.ui")
        self.builder.add_from_file(path)
        self.builder.connect_signals(self)
        self.file_chooser = self.builder.get_object("file_chooser_show")
        self.path = None

        self.create_buttons(type)

    def create_buttons(self, type):
        if type == "save":
            label = _("Save")
            title = _("Save as...")
        elif type == "open":
            label = _("Open")
            title = _("Open")
        else:
            return

        confirm = self.builder.get_object("button_confirm")
        confirm.set_label(label)
        confirm.connect('clicked', self.confirm)
        self.file_chooser.set_action(Gtk.FileChooserAction.SAVE)
        self.file_chooser.set_title(title)

    def confirm(self, widget):
        self.path = self.file_chooser.get_filename()
        self.file_chooser.destroy()

    def run(self):
        self.file_chooser.run()

        if self.file_chooser:
            self.file_chooser.destroy()

    def cancel(self, widget):
        self.file_chooser.destroy()

