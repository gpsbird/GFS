#############################################################################~
#        10/23/2013            								                               #~~
#	Multi-Threaded Chunk Server						                                	    #~~~
#		by									                                                       #~~~~
#	Torrent Glenn & Brendon Walter							                                  #~~~~
#											                                                           #~~~~~
#											                                                            #~~~~~~
####################################################################################~~~~~~~

""" The Chunk Server is a multithreaded server designed to run on multiple server machines it uses the socket libary for connections
with the other members of the GFS; the threading library to ensure that it can handle multiple requests; and the os library to 
manage miscellaneous file counting functions. The main thread listens on the specified port and upon accepting a connection spawns
a distributor thread which parses the first message and hands the connection to the appropriate worker thread""" 

#import all the necessary libraries
import socket
import threading
import os


mg64 = 1024*1024 # 64 megabytes in binary
	
ADDRESS = '' # set address to the local IP
PORT = 9666 # carry out all communications on port 9666

class connThread(threading.Thread): 
	# This class is the parent class from which all other threads inherit 
	# it gives all its child threads connection capabilities
	daemon = True
	def __init__(self,acceptedConn,data=0): # optional data slot in addition to accepted connection
		threading.Thread.__init__(self)
		self.connection = acceptedConn[0] # in the __init__ function the accepted connection is split into connection..
		self.remoteAddress = acceptedConn[1] # ... and a remote address
		self.data = data 

class heartBeatThread(connThread):
	# The heartBeatThread just sends a "<3!" to the master, it is calles with the command "<3?"
	def run(self):
		self.connection.send("<3!")
		self.connection.close()

class chunkSpaceThread(connThread):
	# This is activated by the "chunkSpace?" command. 
	def run(self):
		self.connection.send("continue") # after receiving the connection the thread confirms that it is ready to receive arguments
		chunkHandle = self.connection.recv(1024) # it listens on its connection for a chunkhandle
		emptySpace = mg64 - os.stat(chunkHandle).st_size # then checks the difference between the file's size and 64mg (the max chunk size)
		self.connection.send(emptySpace) # and returns the amount of space left to the API
		self.connection.close() # closes the connection

class chunkReaderThread(connThread):
	# activated by the "Read" command.
	def run(self):
		self.connection.send("continue") # confirms readiness for data
		chunkHandle = self.connection.recv(1024) # listens for chunkHandle
		self.connection.send("continue") # confirmes ready state
		byteOffSet = int(self.connection.recv(1024)) # listes for a byte offset to read from (relative to the beginning of the given chunk)
		self.connection.send("continue") # confirms the desire for EVEN MORE data
		bytesToRead = int(self.connection.recv(1024)) # listens for the number of bytes to read
		chunk = open("chunkHandle") # opens the designated chunk to read from
		chunk.seek(byteOffSet) # goes to the specified byte offset
		fileContent = chunk.read(bytesToRead) # stuffs all the stuff to be read into a variable
		chunk.close() # closes the chunk
		self.connection.close() # closes the connection

##################################### Entering Brendon's Code ####################################
class onPi(connThread):
	path = "Chunks/"
        
        def run(self):
                files = []
                for filenames in os.walk(self.path):
                        files.append(filenames)
                output = str( '|'.join(files[0][2]))
		if output == "":
			self.connection.send(" ")
		else:
			self.connection.send(output)
                
class makeChunk(connThread):
        def run(self):
		self.connection.send("continue")
		print "RAWR"
                chunkHandle = self.connection.recv(1024)
                open("Chunks/"+chunkHandle, 'w').close()
		print "DONE"
class appendChunk(connThread):
	
        def run(self):
		self.connection.send("continue")
		chunkHandle = self.connection.recv(1024)
		self.connection.send("continue")
		data = self.connection.recv(67108864)
                with open("Chunks/"+chunkHandle, 'a') as a:
                        a.write(data)
###################################### Exiting Brendon's Code ###########################################

class distributorThread(connThread):
	# The mighty distributor thread
	def __init__(self,acceptedConn): # it has no data option because its going to make/get the data
		threading.Thread.__init__(self) # call threading.Thread.__init__ in order to initial hethread correctly
		self.connection = acceptedConn # give itself the accepted connection
	def run(self):
		command = self.connection[0].recv(1024) # listens for a command on the connection handed down from the main thread
		# next the distributor hands the connection to the appropriate worker based on the command given, invalid commands simply fall through

		if command == "<3?":
			# in this and each other if/elif statement the correct worker thread is started for a given command
			beat = heartBeatThread(self.connection)
			beat.start()
		elif command == "ChunkSpace?":
			t = chunkSpaceThread(self.connection)
			t.start()
		elif command == "Read":
			t = chunkReaderThread(self.connection)
			t.start()
		elif command == "Contents?":
			t = onPi(self.connection)
			t.start()
		elif command == "makeChunk":
			t = makeChunk(self.connection)
			t.start()
		elif command == "append":
			t = appendChunk(self.connection)
			t.start()
	
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # set up the socket for some TCP action
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # set the reuseaddr option in order to not clog up the port
s.bind((ADDRESS, PORT)) # bind

while 1: # always and forever
	s.listen(1) # listen for incoming connections from the master or API
	t = distributorThread(s.accept()) # if something comes in spawn a distributor thread and hand it off
	t.start() # start the distributor thread
s.close()