from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
		# Create CLOSING GUI button
		self.closing = Button(self.master, width=20, padx=3, pady=3)
		self.closing["text"] = "Close"
		self.closing["command"] =  self.close
		self.closing.grid(row=2, column=1, padx=2, pady=2)


	def setupMovie(self):
		"""Setup button handler."""
		## States cannot set up
		if (self.state == 1 or self.state == 2):
			print("Already SETTING UP....") 
			return

		self.teardownAcked = 0
		self.rtspSeq = self.rtspSeq + 1
		
		## send and recv
		self.sendRtspRequest(requestCode=self.SETUP)
		# dataResponse = self.recvRtspReply()

		# code, self.sessionId = self.parseRtspReply(data=dataResponse)
		time.sleep(0.2)
		if (self.requestSent == 1):
			self.openRtpPort()
			self.state = self.READY
		else:
			print("Error at SetupMovie",'\n')
		
	#DONE

	
	def exitClient(self):
		"""Teardown button handler."""
		if (self.state == self.INIT):
			print("IN INIT....CANNOT TEARDOWN....") 
			return

		self.rtspSeq = self.rtspSeq + 1

		self.sendRtspRequest(requestCode=self.TEARDOWN)
		# dataResponse = self.recvRtspReply()
		# code, self.sessionId = self.parseRtspReply(data=dataResponse)
		time.sleep(0.2)

		if (self.requestSent == 1 ):
			self.teardownAcked = 1
			self.state = self.INIT
			
		else:
			print("Error at teardown",'\n')

		
	#DONE



	def pauseMovie(self):
		"""Pause button handler."""
		if (self.state == self.READY):
			print("READY...CANNOT PAUSE....") 
			return
		if (self.state == self.INIT):
			print("SET UP FIRST....") 
			return

		self.rtspSeq = self.rtspSeq + 1
		
		self.sendRtspRequest(requestCode=self.PAUSE)
		# dataResponse = self.recvRtspReply()
		# code, self.sessionId = self.parseRtspReply(data=dataResponse)
		time.sleep(0.2)

		if (self.requestSent == 1):
			self.playEvent.set()
			self.state = self.READY
		else:
			print("Error at Pause",'\n')

	#DONE
	


	def playMovie(self):
		"""Play button handler."""

		if (self.state == 0):
			print("SET UP FIRST....") 
			return
		if (self.state == 2):
			print("PLAYING....") 
			return

		self.rtspSeq = self.rtspSeq + 1
		self.sendRtspRequest(requestCode=self.PLAY)

		try:
			self.thread.join()
		except:
			traceback.print_exc()

		# dataResponse = self.recvRtspReply()

		# code, self.sessionId = self.parseRtspReply(data=dataResponse)
		time.sleep(0.1)

		if (self.requestSent == 1):
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.thread = threading.Thread(target=self.listenRtp)
			time.sleep(0.1)
			self.thread.start()
			self.state = self.PLAYING
			print("PLAY\n")
		else:
			print("Error at Play",'\n')

	#DONE



	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		
		while True:

			if self.playEvent.isSet():
				print("Listen PAUSE\n")
				break

			if self.teardownAcked == 1:
				print("Listen TEAR\n")

				self.rtpSocket.shutdown(socket.SHUT_RDWR)
				self.rtpSocket.close()
				break

			# dataResponse = self.recvRtspReply()
			if (self.requestSent == -1):
				self.state = self.READY
				print("END VIDEO !!!....READY")
				break

			try:
				data =  self.rtpSocket.recv(999999)
			except:
				pass
				#traceback.print_exc()
			else:
				if (data):
					image_file = self.writeFrame(data)
					self.updateMovie(image_file)
				
	#Done	




	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		packet = RtpPacket()
		packet.decode(data)

		print ( int(packet.seqNum() ) )

		image_file = "image_cache_" + str(self.sessionId) + ".jpg"
		file = open(image_file, "wb")
		file.write(packet.payload)
		file.close()
		
		return image_file
	#DONE
	


	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		image = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = image, height=288) 
		self.label.image = image
	#DONE
		


	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		ServerInfo = (self.serverAddr, self.serverPort)

		self.RTStreamingPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.RTStreamingPsocket.connect(ServerInfo)

		message = 'Hello, server!'
		print(message)

		self.RevEvent = threading.Event()
		self.RevEvent.clear()
		threading.Thread(target=self.recvRtspReply).start()

	##Done
	


	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if (requestCode == 0):
			message = "SETUP " + str(self.fileName) + " RTSP/1.0\n" + "CSeq: " + str(self.rtspSeq) + "\n" + "Transport: RTP/UDP; client_port= " + str(self.rtpPort)
			self.RTStreamingPsocket.sendall(message.encode("utf-8"))
			#print(message)
		elif (requestCode == 1):
			message = "PLAY " + str(self.fileName) + " RTSP/1.0\n" + "CSeq: " + str(self.rtspSeq) + "\n" + "Session: " + str(self.sessionId)
			self.RTStreamingPsocket.sendall(message.encode("utf-8"))
		elif (requestCode == 2):
			message = "PAUSE " + str(self.fileName) + " RTSP/1.0\n" + "CSeq: " + str(self.rtspSeq) + "\n" + "Session: " + str(self.sessionId)
			self.RTStreamingPsocket.sendall(message.encode("utf-8"))
		elif (requestCode == 3):
			message = "TEARDOWN " + str(self.fileName) + " RTSP/1.0\n" + "CSeq: " + str(self.rtspSeq) + "\n" + "Session: " + str(self.sessionId)
			self.RTStreamingPsocket.sendall(message.encode("utf-8"))

	## DONE
	


	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		
		while True:
			if self.RevEvent.isSet():
				print ("Stop Receiver")
				break

			try:
				data = self.RTStreamingPsocket.recv(256)
			except:
				pass
			else:
				if data:
					data= data.decode("utf-8")
					self.parseRtspReply(data=data)


		# data = self.RTStreamingPsocket.recv(256)
		# if data:
		# 	print("\nData received from server:\n" + data.decode("utf-8"))
		# else:
		# 	print ("Cannot received anything from server!!!\n")

		# return data.decode("utf-8")

	###DONE



	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		request = data.split('\n')

		code = request[0].split(' ',1)
		code = code[1]

		sessionID = request[2].split(' ')
		sessionID = sessionID[1]
		
		if (code == "200 OK"):
			self.sessionId = sessionID
			self.requestSent = 1
		
		else:
			self.requestSent = -1
			print(code,'\n')
	## DONE


	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.rtpSocket.bind((self.serverAddr, self.rtpPort))

		print("\nClient open RTP port: ",self.rtpPort)
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)
	### Done

	def close(self):
		"""Handler on explicitly closing the GUI window."""
	
		# close all socket
		if (self.state == self.READY):
			self.rtpSocket.close()
		elif (self.state == self.PLAYING):
			print("STOP when playing")
			self.exitClient()


		# Try to delete all cache
		try:
			files = os.listdir()
			# Loop through the files and delete the .jpg files
			for file in files:
				if file.endswith('.jpg'):
					os.remove(file)

		except:
			pass
		
		try:
			self.playEvent.set()
		except:
			pass
		time.sleep(0.5)
		self.RevEvent.set()
		self.RTStreamingPsocket.close()
		self.master.destroy()
		print("EXIT COMPLETE !!!")
		#DONE


	def handler(self):
		"""Handler on explicitly closing the GUI window."""

		if (self.state == self.READY):
			self.rtpSocket.close()
		elif (self.state == self.PLAYING):
			print("STOP when playing")
			self.rtpSocket.shutdown(socket.SHUT_RDWR)
			self.rtpSocket.close()
			self.playEvent.set()
			self.exitClient()
		
		self.thread.join(1)
		
		# Try to delete all cache
		try:
			files = os.listdir()
			# Loop through the files and delete the .jpg files
			for file in files:
				if file.endswith('.jpg'):
					os.remove(file)
		except:
			pass


		# close all socket
		
		self.RevEvent.set()
		self.RTStreamingPsocket.close()
		self.master.destroy()
		print("EXIT COMPLETE !!!")
		#DONE
