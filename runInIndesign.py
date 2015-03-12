import sublime, sublime_plugin
import time
import os
import socket
import threading
from queue import Queue
import socketserver
import subprocess
import sys
import time
import re
import tempfile

PATH = os.path.dirname(os.path.realpath(__file__))
HOST, PORT = "localhost", 0

class RunInIndesignCommand(sublime_plugin.TextCommand):
	def run(self,edit, command):
		if command== 'run':
			self.runC(self)
		else:
			self.selectTarget()
	def selectTarget(self):
		sett=sublime.load_settings('RunInIndesign.sublime-settings')
		ctarget=sett.get('target','default')
		available=sett.get('available')
		print(available)
		#print (map(lambda c:c['name'],available))
		self.view.window().show_quick_panel([it['name'] for it in available],self.targetSel)
	def targetSel(self,index):
		sett=sublime.load_settings('RunInIndesign.sublime-settings')
		available=[it['identifier'] for it in sett.get('available')][index]
		sett.set('target',available)
		sublime.save_settings('RunInIndesign.sublime-settings')
	def runC(self, edit):
		self.window=self.view.window()
		self.output_view = Cons(self.window)
		self.clear(self.view)
		myF=self.getFile()
		sublime.status_message("Running "+os.path.basename(myF)+ " with Indesign")
		self.output_view.showConsole();
		iR=IndRunner(myF,self.output_view,self.processOtuput)
		sett=sublime.load_settings('RunInIndesign.sublime-settings')
		currentTarget=sett.get('target')
		self.output_view.addText("Running "+os.path.basename(myF)+ " with Indesign "+currentTarget+"\n")
		iR.scanAndFixTargetEngine()
		iR.runWin('.'+currentTarget if currentTarget else '""')
		
		#iR.server.socket.close()
	def getFile(self):
		f=self.view.file_name()
		if f==None or self.view.is_dirty():
			self.window.run_command('save')
			f=self.view.file_name()
		return f
	def saveCurrentViewInTempFile(self, view):
			#
			# Create a temporary file to hold our contents
			#
			tempFile = tempfile.NamedTemporaryFile(suffix = ".jsx", delete = False)

			#
			# Get the contents of the current view
			#
			region = sublime.Region(0, view.size())
			text = view.substr(region)

			tempFile.write(text.encode("utf-8"))
			tempFile.close()

			return tempFile.name
	def markLine(self,view, line_number):
		self.clear(view)
		print(line_number)
		region = view.text_point(line_number-1, 0)
		line = view.line(region)
		view.add_regions(
			'jsx_error', 
			[line], 
			'keyword', 
			'dot', 
			sublime.DRAW_NO_FILL
		)			
	def clear(self,view):
		view.erase_regions('jsx_error')	
	def processOtuput(self):
		#time.sleep(1)
		log=self.output_view.content
		print(log)
		isInError=None
		# finshedOn=None
		# while not isInError:
		# 	print ('ping')
		# print (threading.currentThread())
		# log=self.output_view.content
		isInError=re.search('\[Exited with error\]',log)
		# finshedOn=re.search('\[Finished\]',log)
		
		if isInError:
			try:
				err=re.search('\s+Error:(.+)',log).group(1)
				f=re.search('\s+File:(.+)',log).group(1)
				line=re.search('\s+Line:(\d+)',log).group(1)
				sublime.status_message(err)
				f=f.replace('\\','/')
				v=self.window.find_open_file(f)
				if v==None:
					v=self.window.open_file(f)
				while v.is_loading():
					pass	
				try:	
					l=int(line)
				except ValueError:
					l=0
				self.markLine(v,l)
				self.window.focus_view(v)
			except Exception as e:
				self.output_view.addText('\nCannot get errors: '+str(e))		
		else:
			sublime.status_message("No errors")
class Cons(object):
	def __init__(self,window):
		self.content=''
		self.output_view = window.create_output_panel("console")
		self.window=window

	def addText(self,txt):
		#print (txt)
		str = txt.replace('\r\n', '\n').replace('\r', '\n')
		self.content=self.content+str
		self.output_view.run_command('append', {'characters': str, 'force': True, 'scroll_to_end': True})
	def showConsole(self):
		self.window.run_command("show_panel", {"panel": "output.console"})

class LogServer (socketserver.TCPServer):
	def __init__(self, server_address, RequestHandlerClass, cons, onExit, bind_and_activate=True):
		self.console=cons
		self.onExit=onExit
		socketserver.TCPServer.__init__(self,server_address,RequestHandlerClass)
		return	

class LogRequestHandler(socketserver.BaseRequestHandler):
	
	def handle(self):
		msg=''
		while True:
			data = str(self.request.recv(1024),'utf-8')
			if not data: break
			msg=msg+data
		#print(msg)
		if msg=="<ServerClose/>":
			self.server.onExit()
			self.server.shutdown()
		else:
			self.server.console.showConsole()
			self.server.console.addText(msg)
		
# Encapsulates subprocess.Popen, listens for exit
class AsyncProcess(object):
	def __init__(self, shell_cmd):
		if not shell_cmd:
			raise ValueError("shell_cmd is required")

		if shell_cmd and not isinstance(shell_cmd, str):
			raise ValueError("shell_cmd must be a string")

		self.killed = False

		# Hide the console window on Windows
		startupinfo = None
		if os.name == "nt":
			startupinfo = subprocess.STARTUPINFO()
			#startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

	   
		print (shell_cmd)
		if sys.platform == "win32":
			# Use shell=True on Windows, so shell_cmd is passed through with the correct escaping
			self.proc = subprocess.Popen(shell_cmd, startupinfo=startupinfo, shell=True)
		elif shell_cmd and sys.platform == "darwin":
			# Use a login shell on OSX, otherwise the users expected env vars won't be setup
			self.proc = subprocess.Popen(["/bin/bash", "-l", "-c", shell_cmd], startupinfo=startupinfo, shell=False)

		self.proc.wait()

	def kill(self):
		if not self.killed:
			self.killed = True
			if sys.platform == "win32":
				# terminate would not kill process opened by the shell cmd.exe, it will only kill
				# cmd.exe leaving the child running
				startupinfo = subprocess.STARTUPINFO()
				startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
				subprocess.Popen("taskkill /PID " + str(self.proc.pid), startupinfo=startupinfo)
			else:
				self.proc.terminate()

	def poll(self):
		return self.proc.poll() == None

	def exit_code(self):
		return self.proc.poll()


class IndRunner(object):
	"""docstring for IndRunner"""
	def __init__(self,fileToRun,cons,finis):
		self.finis=finis
		self.winRun=os.path.join(PATH,'utils','runJs.vbs')
		self.jsxRun=os.path.join(PATH,'utils','jsRunner.jsx')
		self.server = LogServer((HOST, PORT),LogRequestHandler,cons,finis)
		self.runFile = fileToRun
		ip, self.port = self.server.server_address
		self.server_thread = threading.Thread(target=self.server.serve_forever, name='Server')
		# Exit the server thread when the main thread terminates
		#self.server_thread.daemon = True

		# self.server_thread.start()
		# print("Server loop running in thread:", self.server_thread.name)

		# while 1:
		# 	try:
		# 		pass
		# 	except KeyboardInterrupt:
		# 		print('Exited')
		# 		break   
	def scanAndFixTargetEngine(self):
		##reset the jsx to be sure
		f=open(self.jsxRun,'r')
		txt=f.read()
		f.close()
		txt=re.sub('#targetengine.+?$','',txt,1,re.M)
		f=open(self.jsxRun,'w')
		f.write(txt)
		f.close()


		f = open(self.runFile,'r')
		incl=re.search('#targetengine.+?$',f.read(),re.M)
		f.close()
		if incl:
			f=open(self.jsxRun,'r')
			txt=f.read()
			f.close()
			txt=incl.group(0)+'\n'+txt
			f=open(self.jsxRun,'w')
			f.write(txt)
			f.close()


	def runWin(self, specif):
		try:
			cmd='cscript "{}" "{}" {:d} {}'.format(self.winRun,self.runFile,self.port,specif)
			print(cmd)
			#cmd='cscript "'++self.winRun+'" "'+	self.runFile+'" '+str(self.port)+' '+specif
			self.server_thread.start()
			self.proc = threading.Thread(target=AsyncProcess, args=(cmd,))
			print('Server started')
			#self.proc=AsyncProcess(cmd)
			#print(self.proc._args)
			self.proc.start()
		except:
			self.server.shutdown()
	def finishRun(self):

		self.finis()
		print('End Server')

			

# if __name__ == '__main__':
# 	iR=IndRunner(os.path.join(PATH,'utils','test.jsx'),cons)
# 	iR.runWin('CC')
		