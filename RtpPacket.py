import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		"""Encode the RTP packet with header fields and payload."""
		timestamp = int(time())
		header = bytearray(HEADER_SIZE)
		#--------------
		# TO COMPLETE
		#--------------
		# Fill the header bytearray with RTP header fields
		
		# header[0] = ...
		# ...
		header[0] = version << 6
		header[1] = pt

		l_seq = seqnum & 255
		h_seg = seqnum >> 8
		header[2] = l_seq
		header[3] = h_seg


		header[4] = (timestamp >> 24) & 0xff
		header[5] = (timestamp >> 16) & 0xff
		header[6] = (timestamp >> 8) & 0xff
		header[7] = timestamp & 0xff

		header[8] = 0
		header[9] = 0
		header[10] = 0
		header[11] = 0

		# Get the payload from the argument
		self.payload = payload
		self.header = header
		


	def decode(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)
	
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload