

import socket
import os
import struct
from datetime import datetime
import csv
import logging
from tqdm import tqdm


log_file = "server_log.csv"

buffer_size=1024




def check_dir():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    new_directory_name = "server-files"
    new_directory_path = os.path.join(current_directory, new_directory_name)

    if not os.path.exists(new_directory_path):
        os.mkdir(new_directory_path)
        os.chdir(new_directory_path)
        print(f"Directory '{new_directory_name}' created successfully.")
    else:
        os.chdir(new_directory_path)  # Change the working directory to the existing directory
        print(f"Directory '{new_directory_name}' already exists.")


def accept_password(conn):
    try:
        correct_password = 'taco'
        conn.send("Please enter the password: ".encode('utf-8'))
        received_password = conn.recv(buffer_size).decode('utf-8')

        if received_password == correct_password:
            conn.send("Password accepted".encode('utf-8'))
            print("Password accepted")
            print(received_password)
            return True
        else:
            print(f"Incorrect password: {received_password}")
            conn.send("Invalid password. Access denied".encode('utf-8'))
            print(received_password)
            return False
    except ConnectionResetError:
        print("Connection reset by the client.")
        return False
    except Exception as e:
        print(f"Error during password acceptance: {str(e)}")
        return False

def clear_socket_non_blocking(server_socket):
    server_socket.setblocking(0)  # Set the socket to non-blocking mode
    while True:
        try:
            data = server_socket.recv(1024)
            if not data:
                break
        except BlockingIOError:
            break  # No more data to receive
    server_socket.setblocking(1)


#This is the server 
# Function to handle file uploads from the client

def receive_file(conn):

    try:
        # Receive the file name length from the client
        file_name_length = struct.unpack("I", conn.recv(4))[0]
        print(f"Received file name length: {file_name_length}")

        # Receive the file name
        file_name = conn.recv(file_name_length).decode('utf-8')
        print(f"Receiving file: '{file_name}'")

        # Send an acknowledgment to the client
        conn.send("1".encode('utf-8'))
        print("Sent acknowledgment to the client")

        # Receive the file size
        file_size = struct.unpack("Q", conn.recv(8))[0]
        print(f"Received file size: {file_size} bytes")

        # Send an acknowledgment to the client
        conn.send("1".encode('utf-8'))
        print("Sent acknowledgment to the client")

        # Create a local file for writing in the current working directory
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("Receiving...")

        while bytes_received < file_size:
            data = conn.recv(1024)  # Adjust the buffer size as needed
            output_file.write(data)
            bytes_received += len(data)
        output_file.close()
        print(f"Received file '{file_name}' and saved it to the current working directory.")
    except Exception as e:
        print(f"Error receiving file: {str(e)}")
    
    










    # Inside your main function, you can add a condition to check for the "upload" command and call the receive_file function
def send_file_list(client_socket):
    try:
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server-files")        
        if os.path.exists(directory) and os.path.isdir(directory):
            file_list = os.listdir(directory)  # Get a list of files in the directory
            file_list_str = "\n".join(file_list)  # Convert the list to a string with newline separators
            client_socket.send(file_list_str.encode('utf-8'))  # Send the list to the client:

        else:

            client_socket.send("No files available.".encode('utf-8'))
    except Exception as e:
        print(f"Error sending file list: {str(e)}")

def server_download(conn):
    try:
        # Send "Command accepted" message
        print("Command accepted")
        conn.send("Command accepted".encode('utf-8'))

        # Receive the file name length
        file_name_length = struct.unpack("h", conn.recv(2))[0]
        print(file_name_length)
        
        # Receive the file name itself
        print(os.getcwd())
        file_name = conn.recv(file_name_length).decode('utf-8')
        print(f"Received file name: {file_name}")
        
        # Construct the full path to the file in the "server-files" directory
        file_path = os.path.join(os.getcwd(), file_name)

        if os.path.isfile(file_path):
            # Send the file size to the client
            conn.send(struct.pack("i", os.path.getsize(file_path)))
            conn.recv(buffer_size)  # Wait for the client's acknowledgment
            print("Sending file...")

            with open(file_path, "rb") as content:
                while True:
                    data = content.read(buffer_size)
                    if not data:
                        break
                    conn.send(data)
            conn.recv(buffer_size)  # Wait for the client's acknowledgment
        else:
            print(f"File '{file_name}' not found in the 'server-files' directory")
            conn.send(struct.pack("i", -1))
    except Exception as e:
        print(f"Error during file download: {str(e)}")


def receive_file_list(server_socket):
    try:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()

        # Receive the length of the data
        data_length_bytes = client_socket.recv(struct.calcsize('!Q'))
        data_length = struct.unpack('!Q', data_length_bytes)[0]

        # Receive the serialized data
        data = b""
        while len(data) < data_length:
            packet = client_socket.recv(data_length - len(data))
            if not packet:
                break
            data += packet

        # Unpack the received data
        file_list_str = struct.unpack(f"{data_length}s", data)[0].decode('utf-8')

        if file_list_str == "No files available.":
            print("No files available on the client.")
        else:
            file_list = file_list_str.split('\n')
            print("Received File List:")
            for filename in file_list:
                print(filename)

        client_socket.close()
    except Exception as e:
        print(f"Error receiving file list: {str(e)}")

def synchronize_with_client(conn):
    client_files = eval(conn.recv(1024).decode('utf-8'))

    server_files = get_server_files()

    files_to_send = {}
    for file, client_timestamp in client_files.items():
        server_timestamp = server_files.get(file, 0)
        if not os.path.exists(file) or client_timestamp > server_timestamp:
            files_to_send[file] = server_timestamp

    conn.send(str(files_to_send).encode('utf-8'))
    conn.close()

def get_server_files():
    server_files = {}
    for file in os.listdir('.'):
        if os.path.isfile(file):
            timestamp = os.path.getmtime(file)
            server_files[file] = timestamp
    return server_files

def main():
    check_dir()
    global conn, buffer_size # Make conn a global variable to be accessible in client_download
    connection_counter = 0
    buffer_size = 1024
    server_ip = "localhost"
    server_port = 8080
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(1)
   
    print("Server is listening for incoming connections...")

    while True:
        conn, addr = server_socket.accept()

        print(f"Connection from {addr}")
    

        


        # Log the connection to a CSV file (provide the 'log_file' variable)
        with open(log_file, mode='a', newline='') as log_csv:
            log_writer = csv.writer(log_csv)
            log_writer.writerow([datetime.now(), addr])




        # Accept the password from the client
        if not accept_password(conn):
            conn.close()
            continue
        clear_socket_non_blocking(conn) #causing error

    
        try:
            
            while True:
                conn.send("Waiting for Command: ".encode('utf-8'))


                command = conn.recv(buffer_size).decode('utf-8')  # Decode the received command
                print(command)
                if command == 'list':
                    print("Handling 'list' command...")
                    send_file_list(conn)
                elif command == 'download':
                #directory = os.path.abspath(os.path.dirname(__file__))
                    server_download(conn)
                elif command =='upload':
                    receive_file(conn)
                elif command =='Sync':
                     synchronize_with_client(conn)

                else:
                    break
        except ConnectionResetError:
            print("Client disconnected.")
            clear_socket_non_blocking(conn)
        finally:
            conn.close()


        #command= None







if __name__ == "__main__":
    main()






















































