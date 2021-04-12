from tkinter import *
import tkinter.messagebox
import tkinter.filedialog
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time
import datetime

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    SWITCHING = 3
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    SWITCH = 4
    LIST = 5
    DESCRIBE = 6
    FORWARD = 7
    BACKWARD = 8

    counter = 0

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.fileList = ""
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.timeInitiated = "0"
        self.videoWeight = "0"
        self.totalFrame = 1
        self.sendRtspRequest(self.LIST)
        self.setupEvent = threading.Event()
        self.playEvent = threading.Event()
        self.buttonEvent = threading.Event()
        self.setupEvent.set()
        self.buttonEvent.set()
        self.createWidgets()

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)

        # Create Progress bar
        self.progressbar = ttk.Progressbar(self.master, orient =  HORIZONTAL, length = 100, mode = 'determinate')
        self.progressbar['value'] = 0
        self.progressbar.grid(row=1, column=0, columnspan=5, sticky=W + E + N + S, padx=2, pady=2)

        # Create Loss rate display
        self.loss_rate = Label(self.master, width=20, padx=3, pady=3)
        self.loss_rate["text"] = "Loss rate: {: .02f}%".format(0)
        self.loss_rate.grid(row=2, column=0, padx=2, pady=2)
        self.loss_rate["font"] = "Helvetica"

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["background"] = 'green'
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["background"] = 'yellow'
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["background"] = 'red'
        self.teardown["command"] = self.teardownMovie
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create Describe button
        self.describe = Button(self.master, width=20, padx=3, pady=3, relief = RIDGE)
        self.describe["text"] = "Describe"
        self.describe["command"] = self.describeMovie
        self.describe.grid(row=2, column=4, padx=2, pady=2)

        # Create FPS display
        self.fps = Label(self.master, width=20, padx=3, pady=3)
        self.fps["text"] = "FPS: {}%".format(0)
        self.fps.grid(row=3, column=0, padx=2, pady=2)
        self.fps["font"] = "Helvetica"

        # Create browse button
        self.browse = Button(self.master, width=20, padx=3, pady=3)
        self.browse["text"] = "Switch"
        self.browse["command"] = self.browseMovie
        self.browse.grid(row=3, column=1, sticky=W + E + N + S, padx=2, pady=2)

        # Dropbar menu
        self.varList = StringVar(self.master)
        self.varList.set(self.fileName)
        print(*self.fileList)
        self.dropbar = OptionMenu(self.master, self.varList, *self.fileList)
        self.dropbar.grid(row=3, column=2, sticky=W + E + N + S, padx=2, pady=2)

        # Create Forward button
        self.forward = Button(self.master, width=20, padx=3, pady=3)
        self.forward["text"] = "Forward"
        self.forward["command"] = self.forwardMovie
        self.forward.grid(row=3, column=3, padx=2, pady=2)

        # Create Backward button
        self.backward = Button(self.master, width=20, padx=3, pady=3)
        self.backward["text"] = "Backward"
        self.backward["command"] = self.backwardMovie
        self.backward.grid(row=3, column=4, padx=2, pady=2)

        threading.Thread(target=self.buttonController, daemon=True).start()

    def browseMovie(self):
        self.teardownMovie()
        print("Browsed file name", self.varList.get())
        self.fileName = self.varList.get()

    def setupMovie(self):
        """Setup button handler."""
        # TODO
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
            self.setupEvent.set()
            self.playEvent.set()

    def teardownMovie(self):
        """Teardown button handler."""
        # TODO
        self.pauseMovie()
        self.sendRtspRequest(self.TEARDOWN)
        self.teardownAcked = 1
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
        except:
            pass
        try:
            rate = float(self.counter / self.frameNbr)
            print('-' * 60 + "\nRTP Packet Loss Rate :" + str(rate) + "\n" + '-' * 60)
        except (ZeroDivisionError):
            print('-' * 60 + "\nRTP Packet Loss Rate :" + "0\n" + '-' * 60)

        self.setupEvent.set()
        self.playEvent.set()
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.counter = 0
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state = self.INIT

    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == self.INIT:
            print("Playing: Set up before playing")
            self.setupEvent.clear()
            self.timeInitiated = str(datetime.datetime.now())
            self.sendRtspRequest(self.SETUP)
            while self.state != self.READY:
                pass
            # self.playMovie()
        # TODO
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            print("Playing Movie")
            self.playEvent.clear()
            self.setupEvent.clear()
            threading.Thread(target=self.listenRtp).start()
            self.sendRtspRequest(self.PLAY)

    def describeMovie(self):
        if self.state == self.READY:
            description = open("description.txt", "w")
            self.sendRtspRequest(self.DESCRIBE)
            time.sleep(0.01)
            description.write("File name: " + self.fileName + "\n" + "RTP Port: "
                                + str(self.rtpPort) + "\n" + "RTSP protocol version: 1.0\n"
                                + "Transport layer protocol: UDP\n" + "Time started: " + self.timeInitiated + "\n"
                                + "Video weight: " + self.videoWeight + " KBytes\n" + "\nCurrent frame: " + str(self.frameNbr) + "\nTotal frame: " + str(self.totalFrame))
            tkinter.messagebox.showinfo('Description', "File name: "
                                        + self.fileName + "\n" + "RTP Port: " + str(self.rtpPort) + "\n" + "RTSP protocol version: 1.0\n"
                                        + "Transport layer protocol: UDP\n" + "Time started: " + self.timeInitiated + '\n'
                                        + "Video weight: " + self.videoWeight + " KBytes\n" + "Current frame: " + str(self.frameNbr) + "\nTotal frame: " + str(self.totalFrame))

    def forwardMovie(self):
        if self.state == self.READY:
            self.sendRtspRequest(self.FORWARD)

    def backwardMovie(self):
        if self.state == self.READY:
            self.sendRtspRequest(self.BACKWARD)

    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO
        startTime = time.time()
        endTime = time.time()
        while True:
            try:
                startTime = time.time()
                data, addr = self.rtpSocket.recvfrom(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    print("||Received Rtp Packet #" + str(rtpPacket.seqNum()) + "|| ")
                    try:
                        if self.frameNbr + 1 != rtpPacket.seqNum():
                            self.counter += 1
                            print("self.frameNbr:", self.frameNbr)
                            print("rtpPacket.seqNum():", rtpPacket.seqNum())
                            print('!' * 60 + "\nPACKET LOSS\n" + '!' * 60)
                        currFrameNbr = rtpPacket.seqNum()
                    except:
                        print("seqNum() error")
                        print('-' * 60)
                        traceback.print_exc(file=sys.stdout)
                        print('-' * 60)

                    if currFrameNbr != self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                    endTime = time.time()
                    self.loss_rate["text"] = "Loss rate: {: .02f}%".format(100 * float(self.counter / self.frameNbr))
                    self.fps["text"] = "FPS: {}".format(int(1/(endTime - startTime)))
                    self.progressbar['value'] = self.frameNbr * 100 / self.totalFrame
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                print("Didn't receive data!")

                if self.playEvent.isSet():
                    print("Continue to click")
                    break

                if self.setupEvent.isSet():
                    break
                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
            if self.teardownAcked == 1:
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # TODO
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        try:
            file = open(cachename, "wb")
        except:
            print("file open error")
        try:
            file.write(data)
        except:
            print("file write error")
        file.close()
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        # TODO
        try:
            photo = ImageTk.PhotoImage(Image.open(imageFile))
        except:
            print("photo error")
            print('-' * 60)
            traceback.print_exc(file=sys.stdout)
            print('-' * 60)

        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        # TODO
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------
        # Get file list request
        if requestCode == self.LIST:
            threading.Thread(target=self.recvRtspReply).start()
            request = "LIST " + "" + "\n" + str(self.rtspSeq) + "\n" + " RTSP/1.0 RTP/UDP " + str(
                self.rtpPort)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            self.requestSent = self.LIST
        # Setup request
        elif requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "SETUP " + str(self.fileName) + "\n" + str(self.rtspSeq) + "\n" + " RTSP/1.0 RTP/UDP " + str(
                self.rtpPort)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SETUP
        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PLAY " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nPLAY request sent to Server...\n" + '-' * 60)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PAUSE " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nPAUSE request sent to Server...\n" + '-' * 60)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
        # Teardown request
        elif requestCode == self.TEARDOWN:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nTEARDOWN request sent to Server...\n" + '-' * 60)
            # Keep track of the sent request.
            self.requestSent = self.TEARDOWN
        # Describe request
        elif requestCode == self.DESCRIBE and self.state == self.READY:
            self.rtspSeq = self.rtspSeq + 1
            request = "DESCRIBE " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nDESCRIBE request sent...\n" + '-' * 60)
            self.requestSent = self.DESCRIBE
        # Forward request
        elif requestCode == self.FORWARD and self.state == self.READY:
            self.rtspSeq = self.rtspSeq + 1
            request = "FORWARD " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nFORWARD request sent...\n" + '-' * 60)
            self.requestSent = self.FORWARD
        # Backward request
        elif requestCode == self.BACKWARD and self.state == self.READY:
            self.rtspSeq = self.rtspSeq + 1
            request = "BACKWARD " + "\n" + str(self.rtspSeq)
            request_byte = request.encode()  # An
            self.rtspSocket.send(request_byte)
            print('-' * 60 + "\nBACKWARD request sent...\n" + '-' * 60)
            self.requestSent = self.BACKWARD
        else:
            return

    # Send the RTSP request using rtspSocket.
    # ...

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        # TODO
        while True:
            try:
                # TODO
                reply = self.rtspSocket.recv(1024)
                if self.requestSent == self.LIST:
                    self.fileList = reply.decode().split(',')[:-1]
                    break
                if reply:
                    self.parseRtspReply(reply)
                # Close the RTSP socket upon requesting Teardown
                if self.requestSent == self.TEARDOWN:
                    self.rtspSocket.shutdown(socket.SHUT_RDWR)
                    self.rtspSocket.close()
                    break
            except:
                pass
            if self.setupEvent.isSet():
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        # TODO
        data_bytes = data.decode()  # An
        lines = data_bytes.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        print("Updating RTSP state...")
                        # self.state = ...
                        self.state = self.READY
                        # Open RTP port.
                        print("Setting Up RtpPort for Video Stream")
                        self.openRtpPort()
                        self.totalFrame = int(lines[4])
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                        print('-' * 60 + "\nClient is PLAYING...\n" + '-' * 60)
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        # self.state = ...
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                    elif self.requestSent == self.DESCRIBE:
                        self.videoWeight = lines[3]

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...

        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket.settimeout(0.5)
        #		try:
        # Bind the socket to the address using the RTP port given by the client user
        # ...
        #		except:
        #			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

        try:
            # self.rtpSocket.connect(self.serverAddr,self.rtpPort)
            self.rtpSocket.bind((self.serverAddr, self.rtpPort))  #  rtpPort# should be bigger than 1024
            # self.rtpSocket.listen(5)
            print("Bind RtpPort Success")

        except:
            pass
            # tkinter.messagebox.showwarning('Connection Failed', 'Connection to rtpServer failed...')

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.sendRtspRequest(self.TEARDOWN)
            self.buttonEvent.clear()
            self.playEvent.set()
            self.setupEvent.set()
            self.master.destroy()  # Close the gui window
            self.teardownAcked = 1
            try:
                dir_name = "./"
                directory = os.listdir(dir_name)

                for file in directory:
                    if file.endswith(CACHE_FILE_EXT) and file.startswith(CACHE_FILE_NAME):
                        os.remove(os.path.join(dir_name, file))
                # os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
            except OSError:
                pass
            # sys.exit(0)
            os._exit(0)

        else:  # When the user presses cancel, resume playing.
            print("Playing Movie")
            threading.Thread(target=self.listenRtp).start()
            self.sendRtspRequest(self.PLAY)

    def buttonController(self):
        while True:
            if self.buttonEvent.isSet():
                if not self.fileName == self.varList.get():
                    self.start["state"] = 'disabled'
                    self.pause["state"] = 'disabled'
                    self.browse["state"] = 'normal'
                else:
                    self.start["state"] = 'normal'
                    self.pause["state"] = 'normal'
                    self.browse["state"] = 'disabled'

                if self.requestSent == self.PLAY:
                    self.dropbar["state"] = "disabled"
                else:
                    self.dropbar["state"] = "normal"

                if self.requestSent == self.PAUSE or self.requestSent == self.DESCRIBE or self.requestSent == self.FORWARD or self.requestSent == self.BACKWARD:
                    self.describe["state"] = "normal"
                    self.forward["state"] = "normal"
                    self.backward["state"] = "normal"
                else:
                    self.describe["state"] = "disabled"
                    self.forward["state"] = "disabled"
                    self.backward["state"] = "disabled"
            else:
                print("thread dies")
                break
