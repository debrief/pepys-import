import sys

if sys.platform != "win32":
    import array
    import fcntl
    import os
    import select
    import termios
    import time

    import pyte

    from pepys_admin.maintenance.gui import MaintenanceGUI

    def run_gui(ds, keys=None, print_output=False):
        """Runs the GUI, sending the given keypresses to the GUI and returning
        a string of the output on the screen.

        Mostly taken from https://mrossinek.gitlab.io/programming/testing-tui-applications-in-python/
        with edits."""
        # create pseudo-terminal
        pid, f_d = os.forkpty()

        if pid == 0:
            # child process spawns TUI
            gui = MaintenanceGUI(ds)
            gui.app.run()
        else:
            buf = array.array("h", [46, 181, 1000, 1000])
            fcntl.ioctl(f_d, termios.TIOCSWINSZ, buf)

            # parent process sets up virtual screen of
            # identical size
            screen = pyte.Screen(181, 46)
            stream = pyte.ByteStream(screen)
            # SEND KEYS
            time.sleep(5)
            if keys is not None:
                if isinstance(keys, list):
                    for key in keys:
                        os.write(f_d, key)
                        os.fsync(f_d)
                else:
                    os.write(f_d, keys)

            # scrape pseudo-terminal's screen
            while True:
                try:
                    [f_d], _, _ = select.select([f_d], [], [], 1)
                except (KeyboardInterrupt, ValueError):
                    # either test was interrupted or the
                    # file descriptor of the child process
                    # provides nothing to be read
                    break
                else:
                    try:
                        # scrape screen of child process
                        data = os.read(f_d, 1024)
                        stream.feed(data)
                    except OSError:
                        # reading empty
                        break
            if print_output:
                for line in screen.display:
                    print(line)

            return "\n".join(screen.display)

else:

    def run_gui():
        pass
