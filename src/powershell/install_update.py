import threading
from time import sleep


def install_windows_update_all_pc(max_computers_per_iteration: int, n_computers: int):
    threads: list[threading.Thread] = []
    for i in range(0, max_computers_per_iteration):
        threads.append(
            threading.Thread(target=install_windows_update, args=(i, max_computers_per_iteration, n_computers)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def install_windows_update(i: int, max_computers_per_iteration: int, n_computers: int):
    for j in range(i, n_computers, max_computers_per_iteration):
        print("Installing Windows Update on pc " + str(j) + "...")
        # TODO: All steps to update a windows pc via ssh and scripts...
        sleep(5)
        print("Windows Update installed successfully")
