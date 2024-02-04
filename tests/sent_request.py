import asyncio
import websockets
import os

async def send_file(uri, file_path):
    # Connect to the WebSocket server
    async with websockets.connect(uri) as websocket:
        # Ensure the file exists
        if not os.path.isfile(file_path):
            print("File not found!")
            return

        # Get file size and name
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Send file metadata
        await websocket.send_json({"name": file_name, "size": file_size})

        # Send the file in chunks
        with open(file_path, 'rb') as file:
            while True:
                # Read the file in chunks (e.g., 4KB at a time)
                bytes_read = file.read(4096)
                if not bytes_read:
                    # File transmitting is done
                    break
                await websocket.send(bytes_read)

        print("File has been sent successfully.")

# Replace with your actual file and WebSocket server URI
file_to_send = "path/to/your/image.png"
server_uri = "ws://localhost:8000/ws/automation"

# Start the event loop and send the file
asyncio.run(send_file(server_uri, file_to_send))
