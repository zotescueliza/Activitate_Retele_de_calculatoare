import socket
import json
import os
import threading
from datetime import datetime

# Configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 5000
FILES_DIR = 'files'
DEFAULT_USER = 'student'
DEFAULT_PASSWORD = '1234'
HISTORY_FILE = 'operation_history.json'

def ensure_files_dir():
    """Ensure files directory exists"""
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
        print(f"✓ Directory '{FILES_DIR}' created")


def authenticate(username, password):
    """Authenticate user"""
    return username == DEFAULT_USER and password == DEFAULT_PASSWORD


def get_history_path():
    """Get full path for operation history file"""
    return os.path.join(FILES_DIR, HISTORY_FILE)


def load_history():
    """Load file operation history"""
    history_path = get_history_path()

    if not os.path.exists(history_path):
        return []

    try:
        with open(history_path, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    """Save file operation history"""
    history_path = get_history_path()

    with open(history_path, 'w') as f:
        json.dump(history, f, indent=4)


def log_operation(operation, filename, user, details=''):
    """Log a file operation"""
    history = load_history()

    history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'operation': operation,
        'filename': filename,
        'user': user,
        'details': details
    })

    save_history(history)


def get_file_history(filename):
    """Get operation history for a specific file"""
    history = load_history()
    file_history = []

    for entry in history:
        if entry.get('filename') == filename:
            file_history.append(entry)

    return file_history


def handle_client(conn, addr):
    """Handle client connection"""
    print(f"\n🔗 Client connected from {addr}")
    authenticated = False
    current_user = None
    
    try:
        while True:
            # Receive request
            request_data = conn.recv(4096).decode('utf-8')
            if not request_data:
                break
            
            try:
                request = json.loads(request_data)
                command = request.get('command')
                
                print(f"📨 Command received: {command}")
                
                # Authentication
                if command == 'login':
                    username = request.get('username')
                    password = request.get('password')
                    
                    if authenticate(username, password):
                        authenticated = True
                        current_user = username
                        response = {'status': 'success', 'message': f'Welcome {username}!'}
                        print(f"✓ User {username} authenticated")
                    else:
                        response = {'status': 'error', 'message': 'Invalid credentials'}
                        print(f"✗ Authentication failed for user {username}")
                
                elif not authenticated:
                    response = {'status': 'error', 'message': 'Not authenticated. Use login first'}
                
                # File operations
                elif command == 'create_file':
                    filename = request.get('filename')
                    content = request.get('content', '')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)

                    log_operation(
                        'create_file',
                        filename,
                        current_user,
                        'File created on server'
                    )
                    
                    response = {'status': 'success', 'message': f'File {filename} created on server'}
                    print(f"✓ File created: {filename}")
                
                elif command == 'upload':
                    filename = request.get('filename')
                    content = request.get('content', '')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)

                    log_operation(
                        'upload',
                        filename,
                        current_user,
                        'File uploaded to server'
                    )
                    
                    response = {'status': 'success', 'message': f'File {filename} uploaded'}
                    print(f"✓ File uploaded: {filename}")
                
                elif command == 'rename_file':
                    old_name = request.get('old_name')
                    new_name = request.get('new_name')

                    old_path = os.path.join(FILES_DIR, old_name)
                    new_path = os.path.join(FILES_DIR, new_name)

                    if not old_name or not new_name:
                        response = {
                            'status': 'error',
                            'message': 'Old filename and new filename are required'
                        }

                    elif not os.path.exists(old_path):
                        response = {
                            'status': 'error',
                            'message': f"File '{old_name}' does not exist"
                        }

                    elif os.path.exists(new_path):
                        response = {
                            'status': 'error',
                            'message': f"File '{new_name}' already exists"
                        }

                    else:
                        os.rename(old_path, new_path)

                        log_operation(
                            'rename_file',
                            new_name,
                            current_user,
                            f"File renamed from '{old_name}' to '{new_name}'"
                        )

                        response = {
                            'status': 'success',
                            'message': f"File '{old_name}' renamed to '{new_name}'"
                        }

                        print(f"✓ File renamed: {old_name} -> {new_name}")
                
                elif command == 'read_file':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)

                    if not filename:
                        response = {
                            'status': 'error',
                            'message': 'Filename is required'
                        }

                    elif not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File '{filename}' does not exist"
                        }

                    else:
                        with open(filepath, 'r') as f:
                            content = f.read()

                        log_operation(
                            'read_file',
                            filename,
                            current_user,
                            'File content read from server'
                        )

                        response = {
                            'status': 'success',
                            'message': f"File '{filename}' read successfully",
                            'content': content
                        }

                        print(f"✓ File read: {filename}")
                
                elif command == 'download':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)

                    if not filename:
                        response = {
                            'status': 'error',
                            'message': 'Filename is required'
                        }

                    elif not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File '{filename}' does not exist"
                        }

                    else:
                        with open(filepath, 'r') as f:
                            content = f.read()

                        log_operation(
                            'download',
                            filename,
                            current_user,
                            'File downloaded from server'
                        )

                        response = {
                            'status': 'success',
                            'message': f"File '{filename}' downloaded successfully",
                            'content': content
                        }

                        print(f"✓ File downloaded: {filename}")
                
                elif command == 'edit_file':
                    filename = request.get('filename')
                    content = request.get('content', '')

                    filepath = os.path.join(FILES_DIR, filename)

                    if not filename:
                        response = {
                            'status': 'error',
                            'message': 'Filename is required'
                        }

                    elif not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File '{filename}' does not exist"
                        }

                    else:
                        with open(filepath, 'w') as f:
                            f.write(content)

                        log_operation(
                            'edit_file',
                            filename,
                            current_user,
                            'File content edited on server'
                        )

                        response = {
                            'status': 'success',
                            'message': f"File '{filename}' edited successfully"
                        }

                        print(f"✓ File edited: {filename}")
                
                elif command == 'see_file_operation_history':
                    filename = request.get('filename')

                    if not filename:
                        response = {
                            'status': 'error',
                            'message': 'Filename is required'
                        }

                    else:
                        history = get_file_history(filename)

                        response = {
                            'status': 'success',
                            'message': f"History for '{filename}'",
                            'history': history
                        }

                        print(f"✓ History sent for: {filename}")
                
                elif command == 'list_files':
                    files = [
                        file for file in os.listdir(FILES_DIR)
                        if file != HISTORY_FILE
                    ]

                    response = {'status': 'success', 'files': files}
                    print(f"✓ Files listed: {len(files)} files found")
                
                elif command == 'logout':
                    authenticated = False
                    current_user = None
                    response = {'status': 'success', 'message': 'Logged out'}
                    print(f"✓ User logged out")
                
                else:
                    response = {'status': 'error', 'message': f'Unknown command: {command}'}
                
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                print(f"✗ Error: {str(e)}")
            
            # Send response
            conn.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
    finally:
        conn.close()
        print(f"🔌 Client disconnected from {addr}")


def start_server():
    """Start FTP server"""
    ensure_files_dir()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    
    print("=" * 60)
    print("🚀 FTP SERVER STARTED")
    print("=" * 60)
    print(f"Host: {SERVER_HOST}")
    print(f"Port: {SERVER_PORT}")
    print(f"Files Directory: {FILES_DIR}")
    print(f"Default User: {DEFAULT_USER}")
    print(f"Default Password: {DEFAULT_PASSWORD}")
    print("=" * 60)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n\n⛔ Server shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    start_server()