#! /bin/env python
#
# Routine to daemonize a process on unix
#
#
DAEMON_HOME = '/'

class NullDevice:
	def write(self, s):
		pass

def daemonize(homeDir = DAEMON_HOME):
	import os
	import sys

	if os.fork() != 0:   				# Parent
		os._exit(0)						# Kill parent

				
	os.chdir(homeDir)					# Detach from parent tty
	os.setsid()							# and start new session
	os.umask(0)
	
	sys.stdin.close()					# Close stdin, stdout
	sys.stdout.close()
	sys.stdin = NullDevice()
	sys.stdout = NullDevice()
	
	for n in range(3, 256):				# Close any remaining file
		try: 							# descriptors
			os.close(n)
		except:
			pass

	if os.fork() != 0:					# finally fork again
		os._exit(0)						# to fully daemonize

	

def spawn(cmd, args):
	import string
	import os
	import sys
	import signal

	# Prevent zombie orphans by ignoring SIGCHLD signal
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	args = string.split(args)
	if os.fork() != 0:					# Calling Parent
		return							# allow this parent to continue running

	os.chdir(DAEMON_HOME)				# Temp Parent
	os.setsid()							# Detach from calling parent
	os.umask(0)							

	if os.fork() != 0:					# Kill temp parent 
		os._exit(0)						# Run cmd in new child
	
	os.execvpe(cmd, [cmd] + args, os.environ)


def createPid(pidPath='/var/run'):
	'''Creates PID file for process'''
	
	import os	
	import sys
	
	currentPid = os.getpid() #Gets PID number
	if not currentPid:
		print 'Could not find PID'
		sys.exit()	
	
	scriptFilename, ext = os.path.splitext(os.path.basename(sys.argv[0])) 
	
	pidFile = '%s.pid' % (scriptFilename) #Creates PIDfile  filename
	pidFilePath = os.path.join(pidPath, pidFile)
	
	f = file(pidFilePath, 'w') #Writes PIDfile name
	print >> f, currentPid
	f.close()

if __name__ == "__main__":
        while True:
                daemonize()
                print "hello world"

