import os

class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
            print('-' * 60 + "\nVideo file : |" + filename + "| read\n" + '-' * 60)
        except:
            print("read " + filename + " error")
            raise IOError
        self.frameNum = 0
        self.frameLength = 0
        self.listframeLength = []

    def nextFrame(self):
        """Get next frame."""
        data = self.file.read(5)  # Get the framelength from the first 5 bytes
        data = bytearray(data)
        if data:
            framelength = int(data) # xx bytes
            self.frameLength = framelength
            self.listframeLength.append(self.frameLength)
            # Read the current frame
            frame = self.file.read(framelength)
            if len(frame) != framelength:
                raise ValueError('incomplete frame data')
            self.frameNum += 1
            print('-' * 10 + "\nNext Frame (#" + str(self.frameNum) + ") length:" + str(framelength) + "\n" + '-' * 10)
            return frame

    def previousFrame(self):
        """Get previous frame"""
        if len(self.listframeLength) != 0:
            self.file.seek(-(self.listframeLength[-1] + 5), os.SEEK_CUR)
            if self.frameNum > 0:
                self.frameNum -= 1
            self.listframeLength.pop()

    def frameNbr(self):
        """Get frame number."""
        return self.frameNum
