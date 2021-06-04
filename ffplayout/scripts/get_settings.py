#!/usr/bin/env python3

from apps.api_player.models import GuiSettings


def run():
    gui_settings = GuiSettings.objects.all()

    print(gui_settings.values())
