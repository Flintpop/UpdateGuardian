from src.server.environnement.server_logs import log, log_error, log_new_lines


done = False


def modify_launch_time():
    print("Modify launch time")
    print("Not implemented yet.")
    modify_settings()


def add_host():
    print("Add host called")
    print("Not implemented yet.")
    modify_settings()


def remove_host():
    print("Remove host called")
    print("Not implemented yet.")
    modify_settings()


def exit_settings():
    global done
    print("Exit settings called")
    done = True


def modify_settings():
    global done
    log_new_lines()
    log("Modifying settings...", print_formatted=False)
    log("Type 'launch time' to modify the launch time of the program.", print_formatted=False)
    log("Type 'add' to add a new host.", print_formatted=False)
    log("Type 'remove' to remove a host.", print_formatted=False)
    log("Type 'exit' to exit the settings menu.\n", print_formatted=False)
    inputs = {
        "launch time": lambda: modify_launch_time(),
        "add": lambda: add_host(),
        "remove": lambda: remove_host(),
        "exit": lambda: exit_settings()
    }
    while not done:
        usr_input: str = input("> ")
        if usr_input not in inputs:
            log_error("Invalid input. Please enter a valid input.\n", print_formatted=False)
        else:
            inputs.get(usr_input, lambda: print("Invalid input."))()
