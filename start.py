#!/usr/bin/env python
import sys
import requests
from distutils.version import StrictVersion

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSystemTrayIcon

from osfoffline.database import drop_db
from osfoffline.gui.qt import OSFOfflineQT
from osfoffline.utils.singleton import SingleInstance
from osfoffline.settings import *

from updater4pyi import upd_source, upd_core
from updater4pyi.upd_iface_pyqt4 import UpdatePyQt4Interface
from updater4pyi.upd_defs import Updater4PyiError


def running_warning():
    warn_app = QApplication(sys.argv)
    QMessageBox.information(None, 'Systray', 'OSF-Offline is already running. Check out the system tray.')
    warn_app.quit()


def start():
    SingleInstance(callback=running_warning)  # will end application if an instance is already running

    # Check for updates first and give user a way to get new version
    try:
        swu_source = upd_source.UpdateGithubReleasesSource(REPO)
        swu_updater = upd_core.Updater(current_version=VERSION,
                                       update_source=swu_source)
        swu_interface = UpdatePyQt4Interface(updater=swu_updater,
                                             progname=NAME,
                                             ask_before_checking=True,
                                             parent=QApplication.instance())
    except Updater4PyiError:
        pass

        # Then, if the current version is too old, close the program
    r = requests.get('https://raw.githubusercontent.com/chennan47/OSF-Offline/feature/auto_updater/deploy/Offline-version.json')

    min_version = r.json()['version']
    if StrictVersion(VERSION) < StrictVersion(min_version):
        # User error message
        warn_app = QApplication(sys.argv)
        QMessageBox.information(
            None,
            "Systray",
            "Your OSF-Offline version is too old that you need to update before you can use."
        )
        warn_app.quit()
        sys.exit(1)

    # Start logging all events
    if '--drop' in sys.argv:
        drop_db()

    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, 'Systray', 'Could not detect a system tray on this system')
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    if not OSFOfflineQT(app).start():
        return sys.exit(1)
    return sys.exit(app.exec_())


if __name__ == "__main__":
    start()
