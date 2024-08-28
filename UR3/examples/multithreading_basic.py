import threading
import time

def get_user_input(input_list, new_data):
    while True:
        # Read three numbers from the user
        numbers = input("Enter three numbers separated by spaces: ").split()
        
        if len(numbers) == 3 and all(n.isdigit() for n in numbers):
            # Update the list with new numbers
            input_list.clear()
            input_list.extend(map(int, numbers))
            new_data[0] = 1
        else:
            print("Please enter exactly three numbers.")

def main_loop(input_list, new_data):
    while True:
        # Do something with the input_list
        if new_data[0] != 0:
            print("Processing list: " + str(input_list) )
            new_data[0] = 0
        else:
            # print("Waiting for user input...")
            pass
        
        # Simulate some processing time
        time.sleep(1)

if __name__ == "__main__":
    input_list = []
    new_data = [0]

    # Start a thread to get user input
    input_thread = threading.Thread(target=get_user_input, args=(input_list, new_data,))
    input_thread.daemon = True
    input_thread.start()

    # Start the main loop
    main_loop(input_list, new_data)
