


import socket
import os
from tqdm import tqdm
import struct






#standard buffer stuff will be changed in main if needed
buffer_size= 1024




def connect_to_server(server_ip, server_port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        print(f"Connected to {server_ip}:{server_port}")
        return client_socket
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

def request_password_from_user():
    password = input("Enter your password: ")
    return password

def clear_socket(client_socket):
    client_socket.setblocking(0)  # Set the socket to non-blocking mode
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
        except BlockingIOError:
            break  # No more data to receive
    client_socket.setblocking(1)
def check_dir():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    new_directory_name = "client_files"
    new_directory_path = os.path.join(current_directory, new_directory_name)

    if not os.path.exists(new_directory_path):
        os.mkdir(new_directory_path)
        os.chdir(new_directory_path)  # Change the working directory to the new directory
        print(f"Directory '{new_directory_name}' created successfully.")
    else:
        os.chdir(new_directory_path)  # Change the working directory to the existing directory
        print(f"Directory '{new_directory_name}' already exists.")

def send_file_list(client_socket):
    try:
        directory = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(directory) and os.path.isdir(directory):
            file_list = os.listdir(directory)

            # Serialize the list of file names using struct
            file_list_bytes = struct.pack(f"{len(file_list)}s", '\n'.join(file_list).encode('utf-8'))

            # Send the length of the serialized data
            data_length = len(file_list_bytes)
            client_socket.send(struct.pack('!Q', data_length))

            # Send the serialized data
            client_socket.send(file_list_bytes)
        else:
            client_socket.send("No files available.".encode('utf-8'))
    except Exception as e:
        print(f"Error sending file list: {str(e)}")




def client_download(client_socket, file_name):
    print(f"Downloading file: {file_name}")
    
    try:
        # Send "download" command to the server
        client_socket.send("download".encode('utf-8'))
    except Exception as e:
        return f"Couldn't make a server request. Make sure a connection has been established. Error: {str(e)}"
    
    try:
        # Wait for the "Command accepted" message from the server
        response = client_socket.recv(buffer_size).decode('utf-8')
        if response != "Command accepted":
            return f"Server did not accept the command. Server response: {response}"
    except Exception as e:
        return f"Error waiting for command acceptance: {str(e)}"


    try:
        # Send the file name length and name
        file_name_encoded = file_name.encode('utf-8')
        client_socket.send(struct.pack("h", len(file_name_encoded)))
        client_socket.send(file_name_encoded)

        # Receive the file size
        file_size = struct.unpack("i", client_socket.recv(4))[0]
        if file_size == -1:
            print("File does not exist. Make sure the name was entered correctly")
            return
        # Send acknowledgment to the server
        client_socket.send("1".encode('utf-8'))

        # Create a local file for writing
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("\nDownloading...")
        while bytes_received < file_size:
            data = client_socket.recv(buffer_size)
            output_file.write(data)
            bytes_received += len(data)
        output_file.close()
        print(f"Successfully downloaded {file_name}")

        # Tell the server that the client is ready to receive the download performance details
        client_socket.send("1".encode('utf-8'))
        # Get performance details
        time_elapsed = struct.unpack("f", client_socket.recv(4))[0]
        print(f"Time elapsed: {time_elapsed}s\nFile size: {file_size} bytes")
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return

def upload_file(client_socket, file_name):
    try:
        # Check if the file exists in the current directory
        if os.path.exists(file_name) and os.path.isfile(file_name):
            # Combine the file name with the current directory to create the file path
            file_path = os.path.join(os.getcwd(), file_name)

            # Send the "upload" command to the server
            print("Sending 'upload' command to the server")
            client_socket.send("upload".encode('utf-8'))

            # Send the file name length and name
            file_name_encoded = file_name.encode('utf-8')
            client_socket.send(struct.pack("I", len(file_name_encoded)))
            client_socket.send(file_name_encoded)

            # Send the file size
            file_size = os.path.getsize(file_path)
            client_socket.send(struct.pack("Q", file_size))

            acknowledgment = client_socket.recv(1).decode('utf-8')

            if acknowledgment == "1":
                # The server is ready to receive the file content
                print("Server is ready to receive file content")

                # Send the file's contents
                print("Sending file contents")
                with open(file_path, "rb") as file:
                    while True:
                        data = file.read(1024)  # Adjust the buffer size as needed
                        if not data:
                            break
                        client_socket.send(data)
                        print(f"Sent {len(data)} bytes of data")

                print(f"File '{file_name}' uploaded successfully.")
            else:
                print("Server is not ready to receive the file content. Aborting upload.")
        else:
            print(f"File '{file_name}' does not exist in the current directory.")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")

def synchronize_with_server(client_socket):


    local_files = check_dir()
    client_socket.send(str(local_files).encode('utf-8'))

    files_to_download = eval(client_socket.recv(1024).decode('utf-8'))

    # Download missing or updated files from the server

    client_socket.close()

def check_dir():
    local_files = {}
    for file in os.listdir('.'):
        if os.path.isfile(file):
            timestamp = os.path.getmtime(file)
            local_files[file] = timestamp
    return local_files




def main():
    server_ip = "localhost"
    server_port = 8080
    client_socket = connect_to_server(server_ip, server_port)
    check_dir()
    if client_socket:
        print("You have successfully connected.")


        password_prompt= client_socket.recv(1024).decode('utf-8')

        print(password_prompt)

        password = request_password_from_user()

        client_socket.send(password.encode('utf-8'))

        # Receive the server's response
        response = client_socket.recv(1024).decode('utf-8')
        print(response)  # Print the response from the server

        if response == "Password accepted": 
            clear_socket(client_socket)
            while True:
        
                response = client_socket.recv(1024).decode('utf-8')
                print(response)
                if response == "Waiting for Command: ":
                    # Continue with other actions
                    
                    while True:
                        print("Choose an action:")
                        print("1. List server files")
                        print("2. Request a file")
                        print("3. Upload a file")
                        print("4. Exit")
                        choice = input("Enter the action number: ")

                        if choice == "1":
                            clear_socket(client_socket)
                            client_socket.send("list".encode('utf-8'))
                            file_list = client_socket.recv(1024).decode('utf-8')
                            print("Files on server:")
                            print(' ')
                            print(' ')
                            print(file_list)
                            print(' ')
                            print(' ')
                            
                        elif choice == "2":
                            clear_socket(client_socket)
                            file_name = input("File Name:")
                            client_download(client_socket, file_name)
                           
                            print (' ')

                        elif choice == '3': 
                           file_path = input("Enter the local file path to upload:")
                           upload_file(client_socket, file_path)
                        elif choice =="4":
                            client_socket.close()
                            print("Shutting down.")
                            break
                        elif choice =='Sync':
                            synchronize_with_server(client_socket)
                    else:
                        print(response)
        else:
            print("Bad password")
            client_socket.close()  # Close the socket to shut down the connection
            print("Shutting down.")


if __name__ == "__main__":
    
    main()






















