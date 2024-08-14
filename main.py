import subprocess
import json
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

import os
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk

class ZLikeWindowSwitcherExtension(Extension):
    def __init__(self):
        super(ZLikeWindowSwitcherExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        MIN_LEN_TO_SEARCH = 0
        items = []
        windows = []

        text = event.get_argument() or ''

        if len(text) >= MIN_LEN_TO_SEARCH:
            windows_str =  subprocess.Popen(
                f'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.List | sed -E -e "s/^\(\'//" -e "s/\',\)$//" | jq .',
                shell=True,
                stdout=subprocess.PIPE
            ).stdout.read().decode()

            windows = json.loads(windows_str)

            if len(windows) == 0:
                items.append(
                    ExtensionResultItem(
                        icon='images/not_found.png',
                        name='None window found',
                        description='Try searching for something else',
                        on_enter=DoNothingAction()
                    )
                )
                return RenderResultListAction(items)

            for window in windows:
                if window["id"]:
                    windowsname = subprocess.Popen(
                        f'gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.GetTitle {window["id"]} | sed -E -e "s/^\(\'//" -e "s/\',\)$//" ',
                        shell=True,
                        stdout=subprocess.PIPE
                    ).stdout.read().decode()

                    icon_name = window["wm_class_instance"]

                    icon_theme = Gtk.IconTheme.get_default()

                    icon_info = icon_theme.lookup_icon(icon_name, 48, 0)

                    try:
                        icon_path = icon_info.get_filename()
                    except AttributeError:
                        icon_path = 'images/ios-default-app-icon.png'

                    items.append(ExtensionResultItem(
                        icon=icon_path,
                        name='Open ' + windowsname,
                        on_enter=ExtensionCustomAction(window["wm_class_instance"], keep_app_open=True)
                    ))
            return RenderResultListAction(items)

        items.append(ExtensionResultItem(
            icon='images/window.svg',
            name='Search for a window by name',
            description=f'Try searching for something longer than {MIN_LEN_TO_SEARCH} characters'
        ))

        return RenderResultListAction(items)

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        instance = event.get_data() or ""
        os.system(f'gdbus call --session --dest org.gnome.Shell --object-path /de/lucaswerkmeister/ActivateWindowByTitle --method de.lucaswerkmeister.ActivateWindowByTitle.activateByWmClassInstance {instance}')


if __name__ == '__main__':
    ZLikeWindowSwitcherExtension().run()
