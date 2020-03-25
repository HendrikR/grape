from gui.graph import Graph
from gui.about import About
from gui.file_chooser import FileChooser
from gui.preferences import Preferences

from lib.logger import Logger
from lib.system import *

from gi.repository import Gtk, Gdk
import os
import sys

class Screen(object):

    def __init__(self, hook=False):
        path = os.path.dirname(__file__)
        path = os.path.join(path, "screen.ui")

        self.logger = Logger()

        self.builder = Gtk.Builder()
        self.builder.add_from_file(path)
        self.builder.connect_signals(self)

        self.screen = self.builder.get_object("screen_show")
        self.notebook = self.builder.get_object("notebook")
        self.statusbar = self.builder.get_object("statusbar")

        self.algorithm = None
        self.create_algorithms_menu()

        ##self.screen.connect('key_press_event', self.keyboard_press)
        self.screen.parent_screen = self

        self.notebook.set_scrollable(True)
        self.notebook.set_group_name("graph")

        tab = None
        if not hook:
            tab = Graph(self.builder, self.tab_changed)
            self.add_notebook_tab(tab)

        self.screen.show_all()

        # HACK
        # For some reason the size of scroll only exist after show_all above
        if tab:
            tab.centralize_scroll()

    def create_algorithms_menu(self):
        menu_algorithms = self.builder.get_object("menu_algorithms")
        classes_algorithms = get_algorithms()

        group = None
        for clss in classes_algorithms:
            name = camelcase_to_text(clss.__name__)
            item = Gtk.RadioMenuItem(group=group, label=name)
            item.connect("toggled", self.menu_algorithms, clss)
            menu_algorithms.append(item)
            group = item

#        group.set_active(True)

    def close_tab(self, tab):
        self.logger.info("Closing screen")
        page_number = tab.get_parent().page_num(tab)
        tab.algorithm_stop()

        if tab.changed:
            self.notebook.set_current_page(page_number)
            title = _("Save changes?")
            message_prefix = _("Your file")
            message_suffix = _("has been changed.\nDo you save its changes?")
            message = message_prefix + " \"" + tab.graph.title + "\" " + message_suffix
            dialog = Gtk.MessageDialog(parent=self.screen,
                                       flags=Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.WARNING, message_format=message)
            dialog.set_title(title)

            save = Gtk.STOCK_SAVE_AS
            if tab.graph.path:
                save = Gtk.STOCK_SAVE

            dialog.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO)
            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_buttons(save, Gtk.ResponseType.YES)

            dialog.show_all()
            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.CANCEL:
                return False
            elif response == Gtk.ResponseType.YES:
                self.menu_file_save(None)

                if tab.changed:
                    return False

        tab.get_parent().remove_page(page_number)
        return True

        # number_of_pages = widget.get_parent().get_n_pages() - 1
        # if number_of_pages == 0:
        #    self.main_quit(widget)

    def current_tab(self):
        current_page_number = self.notebook.get_current_page()
        tab = self.notebook.get_nth_page(current_page_number)
        return tab, current_page_number

    def close_tab_clicked(self, widget):
        self.close_tab(widget)

    def tab_switched(self, widget, tab, page_number):
        self.logger.info("Switch tab")
        menu_file_revert = self.builder.get_object("menu_file_revert")
        tab, page_number = self.current_tab()

        if tab.changed and tab.graph.path:
            menu_file_revert.set_sensitive(True)
        else:
            menu_file_revert.set_sensitive(False)

    def add_notebook_tab(self, tab):
        hbox = Gtk.HBox(False, 0)
        icon_theme = Gtk.IconTheme.get_default()
        close_image = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, 1)

        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)

        style = Gtk.RcStyle()
        #style.xthickness = 0
        #style.ythickness = 0
        btn.modify_style(style)

        hbox.pack_start(Gtk.Label(tab.graph.title), False, False, 0)
        hbox.pack_start(btn, False, False, 0)

        self.notebook.append_page(tab, hbox)
        tab.box = hbox
        last_page = self.notebook.get_n_pages() - 1

        if last_page > 0:
            self.notebook.set_current_page(last_page)

        self.notebook.set_tab_reorderable(tab, True)
        self.notebook.set_tab_detachable(tab, True)

        n = self.notebook.page_num(tab)

        btn.connect_object('clicked', self.close_tab_clicked, tab)

        tab.close_button = btn
        self.notebook.set_current_page(n)

        hbox.show_all()
        self.notebook.show_all()

    def tab_changed(self, tab):
        box = tab.box
        label = box.get_children()[0]

        menu_file_revert = self.builder.get_object("menu_file_revert")

        if tab.changed:
            label.set_label("* " + tab.graph.title)

            if tab.graph.path:
                menu_file_revert.set_sensitive(True)
        else:
            label.set_label(tab.graph.title)
            menu_file_revert.set_sensitive(False)

    def menu_file_new(self, widget):
        self.logger.info("New file")
        tab = Graph(self.builder, self.tab_changed)
        self.add_notebook_tab(tab)

    def menu_file_open(self, widget):
        self.logger.info("Opening file")
        file_chooser = FileChooser("open")
        file_chooser.run()

        if file_chooser.path:
            tab = Graph(self.builder, self.tab_changed)
            tab.graph = tab.graph.open(file_chooser.path)
            tab.area.graph = tab.graph
            tab.changed = False
            self.add_notebook_tab(tab)
            self.tab_changed(tab)
        del file_chooser
        current_page_number = self.notebook.get_current_page()
        tab = self.notebook.get_nth_page(current_page_number)
        return tab, current_page_number

    def menu_file_save(self, widget):
        self.logger.info("Saving file")
        tab, i = self.current_tab()

        if tab:
            if not tab.graph.path:
                self.menu_file_save_as(widget)
            else:
                tab.graph.save(tab.graph.path)
                tab.changed = False
                self.tab_changed(tab)

    def menu_file_save_as(self, widget):
        self.logger.info("Saving file as...")
        tab, i = self.current_tab()

        if tab and self.notebook.get_n_pages() > 0:
            file_chooser = FileChooser("save")
            file_chooser.run()

            if file_chooser.path:
                tab.graph.save(file_chooser.path)

                tab.changed = False
                self.tab_changed(tab)

            del file_chooser
            
    def menu_file_export_graphml(self, widget):
        self.logger.info("Exporting as GraphML")
        tab, i = self.current_tab()
        if tab and self.notebook.get_n_pages() > 0:
            print(tab.graph.to_graphml())

    def menu_file_export_enforce(self, widget):
        self.logger.info("Exporting as ENFORCE")
        tab, i = self.current_tab()
        if tab and self.notebook.get_n_pages() > 0:
            print(tab.graph.to_enforce())

    def menu_file_export_dot(self, widget):
        self.logger.info("Exporting as DOT")
        tab, i = self.current_tab()
        if tab and self.notebook.get_n_pages() > 0:
            print(tab.graph.to_dot())

    def menu_file_export_jsg(self, widget):
        self.logger.info("Exporting as JSG")
        tab, i = self.current_tab()
        if tab and self.notebook.get_n_pages() > 0:
            print(tab.graph.to_jsg())

    def menu_file_revert(self, widget):
        self.logger.info("Reverting file")
        tab, page_number = self.current_tab()

        if tab.changed:
            self.notebook.set_current_page(page_number)
            title = _("Revert changes?")
            message_prefix = _("Revert unsaved changes to document")
            message_suffix = _("?")
            message = message_prefix + " \"" + tab.graph.title + "\" " + message_suffix
            dialog = Gtk.MessageDialog(parent=self.screen,
                                       flags=Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.QUESTION,
                                       message_format=message)
            dialog.set_title(title)

            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_buttons(Gtk.STOCK_REVERT_TO_SAVED, Gtk.ResponseType.YES)

            dialog.show_all()
            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.CANCEL:
                return False
            elif response == Gtk.ResponseType.YES:
                if tab.graph.path:
                    tab.graph = tab.graph.open(tab.graph.path)
                    tab.area.graph = tab.graph
                    tab.changed = False
                    self.tab_changed(tab)
                    tab.queue_draw()

                return True

    def menu_file_close(self, widget):
        self.logger.info("Closing file")
        tab, i = self.current_tab()

        if tab and self.notebook.get_n_pages() > 0:
            self.close_tab(tab)

    def menu_file_quit(self, widget):
        self.logger.info("Menu quit")
        self.screen.event(Gdk.Event(Gdk.EventType.DELETE))
        self.main_quit(widget)

    def menu_edit_undo(self, widget):
        self.logger.info("Undo")
        tab, i = self.current_tab()
        tab.undo()
        
    def menu_edit_redo(self, widget):
        self.logger.info("Redo")
        tab, i = self.current_tab()
        tab.redo()

    def menu_edit_add_vertex(self, widget):
        self.logger.info("Adding vertex")
        tab, i = self.current_tab()

        if tab:
            tab.action = "add_vertex"

    def menu_edit_remove_vertex(self, widget):
        self.logger.info("Removing vertex")
        tab, i = self.current_tab()

        if tab:
            tab.action = "remove_vertex"

    def menu_edit_add_edge(self, widget):
        self.logger.info("Adding edge")
        tab, i = self.current_tab()

        if tab:
            tab.action = "add_edge"
            tab.add_edge()

    def menu_edit_remove_edge(self, widget):
        self.logger.info("Removing edge")
        tab, i = self.current_tab()

        if tab:
            tab.action = "remove_edge"

    def menu_edit_preferences(self, widget):
        self.logger.info("Edditing preferences")
        preferences = Preferences()

    def menu_view_zoom_in(self, widget):
        self.logger.info("Zoom in")
        tab, i = self.current_tab()
        tab.zoom_in()

    def menu_view_zoom_out(self, widget):
        self.logger.info("Zoom out")
        tab, i = self.current_tab()
        tab.zoom_out()

    def menu_view_zoom_default(self, widget):
        self.logger.info("Zoom default")
        tab, i = self.current_tab()
        tab.zoom_default()

    def menu_edit_horizontal_align(self, widget):
        self.logger.info("Horizontal aligned")
        tab, page_number = self.current_tab()

        if tab.graph.selected_vertices() < 2:
            return False
       
        mean = int(sum([x.position[1] for x in tab.graph.selected_vertices()]) / len(tab.graph.selected_vertices()))
        for vertex in tab.graph.selected_vertices():
            vertex.position[1] = mean

        tab.queue_draw()                                    

    def menu_edit_vertical_align(self, widget):
        self.logger.info("Vertical aligned")
        tab, page_number = self.current_tab()

        if tab.graph.selected_vertices() < 2:
            return False

        mean = int(sum([x.position[0] for x in tab.graph.selected_vertices()]) / len(tab.graph.selected_vertices()))

        for vertex in tab.graph.selected_vertices():
            vertex.position[0] = mean

        tab.queue_draw()

    def menu_view_fullscreen(self, widget):
        if widget.get_active():
            self.screen.fullscreen()
            self.logger.info("Fullscreen mode ON")
        else:
            self.screen.unfullscreen()
            self.logger.info("Fullscreen mode OFF")

    def menu_view_statusbar(self, widget):
        """Menu view status bar, alternate beetween show and hide statusbar"""
        if widget.active:
            self.statusbar.show()
            self.logger.info("Statusbar show")
        else:
            self.statusbar.hide()
            self.logger.info("Statusbar hide")

    def menu_algorithms(self, widget, algorithm):
        """ When the algorithm is changed"""
        self.algorithm = algorithm

    def menu_algorithms_previous(self, widget):
        """Action of algorithm execution previous"""
        tab, number = self.current_tab()
        self.logger.info("Previous state algorithm")
        tab.algorithm_prev()

    def menu_algorithms_stop(self, widget):
        """Action of algorithm execution stop"""
        tab, number = self.current_tab()
        self.logger.info("Stop algorithm")
        tab.algorithm_stop()
        for place in ["menu_algorithms_", "toolbutton_"]:
            for btn in ["previous", "stop", "pause", "play", "next"]:
                self.builder.get_object(place + btn).set_sensitive(False)
            self.builder.get_object(place + "load").set_sensitive(True)

    def menu_algorithms_load(self, widget):
        tab, number = self.current_tab()
        self.logger.info("Load an algorithm")
        if not self.algorithm:
            return
        reload_algorithm(self.algorithm.__name__)
        tab.algorithm_load(self.algorithm)
        for place in ["menu_algorithms_", "toolbutton_"]:
            for btn in ["previous", "stop", "pause", "play", "next"]:
                self.builder.get_object(place + btn).set_sensitive(True)
            self.builder.get_object(place + "load").set_sensitive(False)
        
    def menu_algorithms_play(self, widget):
        """Action of algorithm execution play"""
        tab, number = self.current_tab()
        self.logger.info("Start algorithm")
        tab.algorithm_play()
        for place in ["menu_algorithms_", "toolbutton_"]:
            for btn in ["previous", "play", "next"]:
                self.builder.get_object(place + btn).set_sensitive(False)
            self.builder.get_object(place + "pause").set_sensitive(True)

    def menu_algorithms_pause(self, widget):
        """Action of algorithm execution next"""
        tab, number = self.current_tab()
        self.logger.info("Pause algorithm")
        tab.algorithm_pause()
        for place in ["menu_algorithms_", "toolbutton_"]:
            for btn in ["previous", "play", "next"]:
                self.builder.get_object(place + btn).set_sensitive(True)
            self.builder.get_object(place + "pause").set_sensitive(False)
        
    def menu_algorithms_next(self, widget):
        """Action of algorithm execution next"""
        tab, number = self.current_tab()
        self.logger.info("Next state algorithm")
        tab.algorithm_()

    def menu_algorithms_layout(self, widget):
        """Action of algorithm execution layout"""
        tab, number = self.current_tab()
        self.logger.info("Layout")
        tab.algorithm_layout()
        
    def menu_help_about(self, widget):
        self.logger.info("About")
        About()

    def keyboard_press(self, widget, event):
        self.logger.info("Key press %s" % event.keyval)
        tab, i = self.current_tab()

        key = event.keyval
        direction = None

        if key == Gdk.KEY_Right:
            direction = "right"
        elif key == Gdk.KEY_Left:
            direction = "left"
        elif key == Gdk.KEY_Up:
            direction = "up"
        elif key == Gdk.KEY_Down:
            direction = "down"
        elif key == Gdk.KEY_Escape:
            if tab.action:
                tab.action = None
            else:
                tab.graph.clear_selection()
                self.logger.info("Clean UP selection")
        elif (event.state & Gdk.ModifierType.CONTROL_MASK):
            if key == Gdk.KEY_A or key == Gdk.KEY_a:
                self.logger.info("Selection all")
                tab.graph.select_all()

        if tab and direction:
            tab.graph.move_selection(direction)
            self.logger.info("Moving selection")

        if tab:
            tab.queue_draw()

    def move_screen(self, x, y):
        self.screen.move(x, y)

    def main_quit(self, widget):
        self.screen.destroy()

