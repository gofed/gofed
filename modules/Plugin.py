from modules.Base import Base
import json
from os import walk
from modules.Config import Config

class Plugin(Base):

	def __init__(self, plugin_path):
		Base.__init__(self)
		self.err = []
		self.plugin_path = plugin_path
		self.plugin_json = {}

	def get(self):
		return self.plugin_json

	def parse(self):
		# read plugin
		if not self.read():
			return False

		# validate plugin
		if not self.validate():
			return False

		return True

	def read(self):
		try:
			with open(self.plugin_path, "r") as fd:
				json_content = fd.read()
			self.plugin_json = json.loads(json_content)
		except Exception, e:
			self.err.append("%s: %s\n" % (self.plugin_path, e))
			return False

		return True

	def validate(self):
		# plugin name exists?
		if "name" not in self.plugin_json.keys():
			self.err.append("%s: missing name field" % self.plugin_path)
			return False
		# commands exists?
		if "commands" not in self.plugin_json.keys():
			self.err.append("%s: missing commands field" % self.plugin_path)
			return False

		for command in self.plugin_json["commands"]:
			if "command" not in command.keys():
				self.err.append("%s: missing command field" % self.plugin_path)
				return False
			if "help" not in command.keys():
				self.err.append("%s: missing help field" % self.plugin_path)
				return False
			if "script" not in command.keys():
				self.err.append("%s: missing script field" % self.plugin_path)
				return False

		return True


class PluginCmd:

	def __init__(self, script):
		self.script = script
		self.interpret = "python"
		self.interactive = False

	def getScript(self):
		return self.script

	def setInterpret(self, interpret):
		self.interpret = interpret

	def getInterpret(self):
		return self.interpret

	def setInteractive(self, interactive):
		self.interactive = interactive

	def isInteractive(self):
		return self.interactive


class Plugins(Base):

	def __init__(self):
		self.err = []
		self.plugins = {}

	def getHelp(self):
		help = {}
		for name in self.plugins:
			plugin = self.plugins[name].get()
			for command in plugin["commands"]:
				cmd = command["command"]
				hlp = command["help"]
				help[cmd] = hlp
		return help

	def getCommandList(self):
		cmd_list = {}
		for name in self.plugins:
			pl_name = name.split(".")[0]
			cmd_list[pl_name] = []
			plugin = self.plugins[name].get()
			for cmd_desc in plugin["commands"]:
				cmd_list[pl_name].append(cmd_desc["command"])
		return cmd_list

	def getCommand(self, command):
		for name in self.plugins:
			plugin = self.plugins[name].get()
			for cmd_desc in plugin["commands"]:
				if cmd_desc["command"] == command:
					plugin_cmd = PluginCmd(cmd_desc["script"])
					if "interpret" in cmd_desc:
						plugin_cmd.setInterpret(cmd_desc["interpret"])
					return plugin_cmd
		return None


	def read(self):
		# TODO: save plugins directory path to config file
		#golang_plugin_path = "/home/jchaloup/Projects/gofed/gofed/plugins"
		golang_plugin_path = Config().getGolangPlugins()
		for dirName, _, fileList in walk(golang_plugin_path): 
			for file in fileList:
				if not file.endswith(".json"):
					continue
				json_file = "%s/%s" % (dirName, file)
				plugin_obj = Plugin(json_file)
				if not plugin_obj.parse():
					self.err += plugin_obj.getError()
					return False
				self.plugins[file] = plugin_obj
		return True
