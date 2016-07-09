import optparse
import yaml
import logging

# TODO(jchaloup): generate class definition for each cmd instead
#                 of reading the yaml files every time a cmd is executed

class OptionParserGenerator(object):

	def __init__(self, definitions = []):
		self._definitions = definitions
		self._parser = None
		self._options = None
		self._args = None

		self._non_empty_flags = []

	def generate(self):
		flags = {}
		for definition in self._definitions:
			with open(definition, 'r') as f:
				# Don't catch yaml.YAMLError
				data = yaml.load(f)
				for flag in data["flags"]:
					flags[flag["long"]] = flag

		self._parser = optparse.OptionParser("%prog")

		for long in sorted(flags.keys()):
			option = flags[long]
			short = ""
			if "short" in option:
				short = "-%s" % option["short"]

			if option["type"] == "boolean":
				action = "store_true"
			else:
				action = "store"

			self._parser.add_option(
				"",
				short,
				"--%s" % option["long"],
				dest=option["target"],
				action=action,
				default = option["default"],
				help = option["description"]
			)

			if "non-empty" in option:
				self._non_empty_flags.append(option)

		return self

	def parse(self):
		self._options, self._args = self._parser.parse_args()
		return self

	def check(self):
		options = vars(self._options)
		for flag in self._non_empty_flags:
			if options[flag["target"]] == "":
				logging.error("Option '--%s' not set. Check command's help" % flag["long"])
				return False
		return True

	def options(self):
		return self._options

	def args(self):
		return self._args

if __name__ == "__main__":
	OptionParserGenerator(["repo2gospec-global.yml", "repo2gospec.yml"]).generate().parse().check()

