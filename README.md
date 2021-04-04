# Simple-Python-Video-Streaming-Application
This is a Client - Server type of Video streaming application in Python. It is an assignment in the Computer Networks subject I took at the Ho Chi Minh University of Technology.

## How to use:
### In a terminal, start the server with the command line:
    python Server.py server_port
<blockquote>
  Where <strong>server_port</strong> is the port your server listens to for incoming RTSP connections. The standard port is 554, but we need to use a port that is greater than 1024.
</blockquote>

### In another terminal, we start a client by typing:
    python ClientLauncher.py server_host server_port RTP_port video_file
<blockquote>
  Where:
  <ul>
    <li><strong>server_host</strong> is the ip of  the machine that the server is running.</li>
    <li><strong>server_port</strong> is the port the client is listening on.</li>
    <li><strong>RTP_port</strong> is the port that the RTP packets are received.</li>
    <li><strong>video_file</strong> is the file you wish to watch (here we use a mjpeg file).</li>
  </ul>
</blockquote>

## Exmaple:
### Start the server:
    python Server.py 1025

### Start the client:
    python ClientLauncher.py 127.0.0.1 1025 5008 movie.mjpeg
