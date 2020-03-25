from gui.screen import Screen
from gi.repository import Gtk, Gdk
import os
import sys
import locale
import gettext

from lib.logger import Logger


class Main(object):
    """Grape GUI main class"""
    def __init__(self):
        """Initializes the interface"""
        # logger
        self.logger = Logger()


        # Refresh interface list
        Gdk.threads_init()
        Gdk.threads_enter()

        self.screens = []
        self.builder = Gtk.Builder()
        self.domain = self.translate()
        self.builder.set_translation_domain(self.domain)
        ##TODOGtk.notebook_set_window_creation_hook(self.screen_create, None)
        self.screen_create()
      
        Gtk.main()
        Gdk.threads_leave()

    def screen_create(self, source=None, page=None, x=None, y=None, user_data=None):
        self.logger.info("Creating screen")
        screen = Screen(page != None)
        if x and y:
            screen.move_screen(x, y)

        screen.screen.connect('delete-event', self.screen_deleted)
        self.screens.append(screen.screen)

        return screen.notebook

    def screen_deleted(self, widget, event):
        self.logger.info("Deleting screen")
        screen = widget.parent_screen

        for i in range(screen.notebook.get_n_pages()):
            tab = screen.notebook.get_nth_page(0)
            if not screen.close_tab(tab):
                return True

        if screen.notebook.get_n_pages() > 0:
            return True

        self.screens.remove(widget)

        if len(self.screens) == 0:
            Gtk.main_quit()

        return False

    def translate(self):
        domain = "grape"
        current_path = os.path.dirname(__file__)
        locale_path = os.path.join(current_path, "..", "..", "..", "config", "locale")

        langs = []
        lc, encoding = locale.getdefaultlocale()

        if (lc):
            langs = [lc]

        language = os.environ.get('LANGUAGE', None)

        if (language):
            langs += language.split(":")

        # TODO - Configuration file
        langs += ["pt_BR", "en_US"]

        gettext.bindtextdomain(domain, locale_path)
        gettext.textdomain(domain)
        lang = gettext.translation(domain, locale_path, languages=langs, fallback = True)

        gettext.install(domain, locale_path)

        return domain

