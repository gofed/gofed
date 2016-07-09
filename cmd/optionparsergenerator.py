import optparse
import yaml
import logging
import re

# TODO(jchaloup): generate class definition for each cmd instead
#                 of reading the yaml files every time a cmd is executed

class OptionParserGenerator(object):

	def __init__(self, definitions = []):
		self._definitions = definitions
		self._parser = None
		self._options = None
		self._args = None
		self._flags = {}

		self._non_empty_flags = []
		self._non_empty_flag_groups = {}

	def generate(self):

		def long2target(long):
			return re.sub(r'[-_]', '', long)

		self._flags = {}
		for definition in self._definitions:
			with open(definition, 'r') as f:
				# Don't catch yaml.YAMLError
				data = yaml.load(f)
				for flag in data["flags"]:
					if "target" not in flag:
						flag["target"] = long2target(flag["long"])

					if "default" not in flag:
						if flag["type"] == "boolean":
							flag["default"] = False
						else:
							flag["default"] = ""

					self._flags[flag["target"]] = flag

		self._parser = optparse.OptionParser("%prog")

		for target in sorted(self._flags.keys()):
			option = self._flags[target]
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

			if "non-empty-group" in option:
				try:
					self._non_empty_flag_groups[option["non-empty-group"]].append(option)
				except KeyError as e:
					self._non_empty_flag_groups[option["non-empty-group"]] = [option]

			if "non-empty" in option:
				self._non_empty_flags.append(option)

		return self

	def parse(self):
		self._options, self._args = self._parser.parse_args()
		return self

	def check(self):
		options = vars(self._options)

		options_on = []

		def is_option_set(options, flag):
			if flag["type"] == "boolean":
				if options[ flag["target"] ]:
					return True
			# the rest assumed to be string
			else:
				if options[ flag["target"] ] != "":
					return True

			return False

		# check required grouped flags first
		for group in self._non_empty_flag_groups:
			group_set = False
			for flag in self._non_empty_flag_groups[group]:
				if is_option_set(options, flag):
					group_set = True
					options_on.append( flag["target"] )
			if not group_set:
				group_options = ", ".join(map(lambda l: "--%s" % l["long"], self._non_empty_flag_groups[group]))
				logging.error("At least one of '%s' options must be set" % group_options)
				return False

		# check required single flags then
		for flag in self._non_empty_flags:
			if not is_option_set(options, flag):
				logging.error("Option '--%s' not set. Check command's help" % flag["long"])
				return False
			options_on.append( flag["target"] )

		# and make sure all required flags has their own required flags set
		count = len(options_on)
		index = 0
		while index < count:
			option = options_on[index]
			if "requires" in self._flags[option]:
				for item in self._flags[option]["requires"]:
					if not is_option_set(options, self._flags[item]):
						logging.error("Option '--%s' not set. Check command's help" % self._flags[item]["long"])
						return False

				options_on = options_on + self._flags[option]["requires"]
				count = count + len(self._flags[option]["requires"])

			index = index + 1

		return True

	def options(self):
		return self._options

	def args(self):
		return self._args

if __name__ == "__main__":
	OptionParserGenerator(["repo2gospec-global.yml", "repo2gospec.yml"]).generate().parse().check()

