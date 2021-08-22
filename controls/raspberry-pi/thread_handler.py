"""
Authors: Manuel Gasser, Julian Haldimann
Created: 01.05.2021
Last Modified: 08.05.2021
"""

import threading

locks = {
    "print_lock": threading.Lock(),
    "pub_lock": threading.Lock(),
    "engine_halt_lock": threading.Lock(),
    "engine_reset_lock": threading.Lock(),
    "engine_stop_lock": threading.Lock(),
    "engine_update_lock": threading.Lock(),
    "serial_lock": threading.Lock(),
    "serial_read_lock": threading.Lock()

}

"""
Start a new thread with a given function and arguments.

:param func: Function that should be executed inside the thread
:param args: Additional argument
:returns: started thread
"""


def start_thread(func, args):
    # Define thread
    thread = threading.Thread(target=func, args=args)
    thread.daemon = True

    # Start thread
    thread.start()

    return thread


"""
Thread safe print function
"""


def s_print(*a, **b):
    with locks["print_lock"]:
        print(*a, **b)
