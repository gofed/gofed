#!/bin/python

# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import optparse
from modules.GoSymbols import getSymbolsForImportPaths, PackageToXml, ProjectToXml

def compareNames(names1, names2):

	names1_set = set(map(lambda i: i.get('value'), names1))
	names2_set = set(map(lambda i: i.get('value'), names2))

	new_names = list(names2_set - names1_set)
	rem_names = list(names1_set - names2_set)

	if new_names != []:
		print "New names: " + ", ".join(new_names)

	if rem_names != []:
		print "Removed names: " + ", ".join(rem_names)

class CompareTypes:

	def __init__(self, debug=False):
		self.debug = debug

	def compareIdents(self, ident1, ident2):
		"""
		Identifier is defined by type (def attribute) and name (name attribute).
		Name attribute is presented only for the top most definitions.

		Both identifiers are identical if their names (if presented) and defs are the same.

		ident1, ident2: etree.Element nodes
		"""
		#<field type="ident" def="string"[ name="Action"]/>
		err = []

		if ident1.get("def") != ident2.get("def"):
			err.append("identifiers differ in type: %s != %s" % (ident1.get("def"), ident2.get("def")))

		if "name" in ident1.keys() and "name" in ident2.keys():
			if ident1.get("name") != ident2.get("name"):
				err.append("identifiers differ in name: %s != %s" % (ident1.get("name"), ident2.get("name")))

			if self.debug:
				print "#NAME: " + ident1.get("name")

		return err

	def comparePointers(self, pointer1, pointer2):
		"""
		Pointer is defined by a type it points to.
		Type is a child element.

		pointer1, pointer2: etree.Element nodes
		"""
		# <field type="pointer" name="Node">
		return self.compareTypes(pointer1[0], pointer2[0])

	def compareSelectors(self, selector1, selector2):
		"""
		Selector is defined by prefix and item.

		expression.selector

		Two selectors are identical if they have the same
		expression (prefix tag) and selector (item tag).

		Expression is always identifier.
		"""
		err = []

		prefix1, prefix2 = None, None
		item1, item2 = None, None

		for node in selector1:
			if node.tag == "prefix":
				prefix1 = node
			elif node.tag == "item":
				item1 = node

		for node in selector2:
			if node.tag == "prefix":
				prefix2 = node
			elif node.tag == "item":
				item2 = node

		if prefix1.get("value") != prefix2.get("value"):
			err.append("Selectors differ in selector: %s != %s" %
			(prefix1.get("value"), prefix2.get("value")))

		if item1.get("value") != item2.get("value"):
			err.append("Selectors differ in expression: %s != %s" %
			(item1.get("value"), item2.get("value")))

		return err

	def compareChannels(self, chan1, chan2):
		"""
		Channel is defined by a direction (dir attribute)
		and type (type tag).

		Channels are identical if their direction and type
		are identical.

		chan1, chan2: etree.Element nodes
		"""
		#<field type="chan" dir="3" name="stop">
		#  <type type="struct" name=""/>
		#</field>
		err = []

		if chan1.get("dir") != chan2.get("dir"):
			err.append("Channels has different direction:"
			  " %s != %s" % (chan1.get("dir"), chan2.get("dir")))

		e = self.compareTypes(chan1[0], chan2[0])
		if e != []:
			err += e

		return err	

	def compareSlices(self, slice1, slice2):
		"""
		Slice is defined by element type (elmtype tag).

		Slices are identical if element types are identical.
		"""
		# <elmtype type="ident" def="string"/>
		return self.compareTypes(slice1[0], slice2[0])

	def compareMaps(self, map1, map2):

		"""
		Map is defined by a keytype (keytype tag) and
		valuetype (valuetype tag).

		Two maps are identical if keytypes and valuetypes
		are identical.

		map1, map2: etree.Element nodes
		"""
		err = []

		value1, value2 = None, None
		key1, key2 = None, None

		for node in map1:
			if node.tag == "keytype":
				key1 = node
			elif node.tag == "valtype":
				value1 = node

		for node in map2:
			if node.tag == "keytype":
				key2 = node
			elif node.tag == "valtype":
				value2 = node

		e = self.compareTypes(key1, key2)
		if e != []:
			err += e

		e = self.compareTypes(value1, value2)
		if e != []:
			err += e

		return err

	def compareFunctions(self, function1, function2):
		"""
		Function is defined by signature.
		Signature consists of:
		  methods' name (name attribute)
		  list of parameters (<paramsList>)
		  list of results (<resultsList>)

		Two functions are identical if their signatures are identical.

		function1, function2: etree.Element nodes

		"""
		#<type name="InterruptHandler" type="func">
		#   <paramsList/>
		#   <resultsList/>
		#</type>
		err = []

		# check names
		if function1.get("name") != function2.get("name"):
			err.append("Function's name differs: %s != %s" %
				(function1.get("name"), function2.get("name")))
			return err

		params1 = None
		params2 = None
		results1 = None
		results2 = None

		for node in function1:
			if node.tag == "paramsList":
				params1 = node
			elif node.tag == "resultsList":
				results1 = node
		for node in function2:
			if node.tag == "paramsList":
				params2 = node
			elif node.tag == "resultsList":
				results2 = node

		# check parameters
		if len(params1) != len(params2):
			err.append("Functions differs in parameter count")
			return err

		for i in range(0, len(params1)):
			e = self.compareTypes(params1[i], params2[i])
			if e != []:
				err += e

		# check results
		if len(results1) != len(results2):
			err.append("Functions differs in result count")
			return err

		for i in range(0, len(results1)):
			e = self.compareTypes(results1[i], results2[i])
			if e != []:
				err += e

		return err

	def compareMethods(self, method1, method2):
		"""
		Method is defined by signature.
		Signature consists of:
		  methods' name (name attribute)
		  reciever
		  list of parameters (<paramsList>)
		  list of results (<resultsList>)

		Two methods are identical if their signatures are identical.

		method1, method2: etree.Element nodes
		"""

		err = []

		# check names
		if method1.get("name") != method2.get("name"):
			err.append("Method's name differs: %s != %s" %
				(method1.get("name"), method2.get("name")))
			return err

		params1 = None
		params2 = None
		results1 = None
		results2 = None

		for node in method1:
			if node.tag == "paramsList":
				params1 = node
			elif node.tag == "resultsList":
				results1 = node
			else:
				print "method receiver tag????"

		for node in method2:
			if node.tag == "paramsList":
				params2 = node
			elif node.tag == "resultsList":
				results2 = node
			else:
				print "method receiver tag????"

		# check parameters
		if len(params1) != len(params2):
			err.append("Methods differs in parameter count")
			return err

		for i in range(0, len(params1)):
			e = self.compareTypes(params1[i], params2[i])
			if e != []:
				err += e

		# check results
		if len(results1) != len(results2):
			err.append("Methods differs in result count")
			return err

		for i in range(0, len(results1)):
			e = self.compareTypes(results1[i], results2[i])
			if e != []:
				err += e

		# check receivers?
		return err

	def compareInterfaces(self, interface1, interface2):

		err = []
		if self.debug:
			print "#INTERFACE: %s" % interface1.get("name")

		m1_set = set(map(lambda m: m.get("name"), interface1[:]))
		m2_set = set(map(lambda m: m.get("name"), interface2[:]))

		new_ms = list(m2_set - m1_set)
		rem_ms = list(m1_set - m2_set)
		com_ms = list(m1_set & m2_set)

		if new_ms != []:
			print "New methods: " + ", ".join(new_ms)

		if rem_ms != []:
			err.append("Interface %s removed methods: %s" %
				(interface1.get("name"), ", ".join(rem_ms)))

		m1s_dir = {}
		m2s_dir = {}
		for method in interface1:
			name = method.get("name")
			if name in com_ms:
				m1s_dir[name] = method

		for method in interface2:
			name = method.get("name")
			if name in com_ms:
				m2s_dir[name] = method

		for method_name in com_ms:
			e = self.compareMethods(m1s_dir[method_name],
				m2s_dir[method_name])
			if e != []:
				err += e

			if self.debug:
				print "#METHOD: %s" % method_name

		return err

	def compareTypes(self, type1, type2):
		err = []
		type = type1.get("type")
		if type != type2.get("type"):
			err.append("Type differs")
			return err

		#print type
		if type == "interface":
			return self.compareInterfaces(type1, type2)
		elif type == "ident":
			return self.compareIdents(type1, type2)
		elif type == "pointer":
			return self.comparePointers(type1, type2)
		elif type == "selector":
			return self.compareSelectors(type1, type2)
		elif type == "chan":	
			return self.compareChannels(type1, type2)
		elif type == "slice":
			return self.compareSlices(type1, type2)
		elif type == "map":
			return self.compareMaps(type1, type2)
		elif type == "struct":
			return self.compareStructs(type1, type2)
		elif type == "func":
			return self.compareFunctions(type1, type2)
		else:
			print "%s type not implemented yet" % type
			exit(0)
			return []

		return []

	def constructTypeQualifiedName(self, type, full=False):
		"""
		For given type construct its full qualified name.

		AnonymousField = [ "*" ] TypeName .
		TypeName  = identifier | QualifiedIdent .
		QualifiedIdent = PackageName "." identifier .
		"""
		t = type.get("type")
		if t == "ident":
			if self.debug:
				print "#FQN: %s" % type.get("def")
			return type.get("def")
		elif t == "pointer":
			return self.constructTypeQualifiedName(type[0])
		elif t == "selector":
			expr, sel = None, None
			for node in type:
				if node.tag == "prefix":
					expr = node.get("value")
				elif node.tag == "item":
					sel = node.get("value")
			if full:
				return "%s.%s" % (expr, sel)
			else:
				return sel
		else:
			print "Type %s can not be used for FQN" % t
			return ""

	def compareStructs(self, struct1, struct2):
		"""
		Struct is defined by its fields.
		Field consists of a name (name attribute) and type definition.

		Order of fields is important but can be different.

		For anonymous field an unqualified type name is taken.

		Structs are identical if they have the same number of fields
		and list of fiels are identical.

		struct1, struct2: etree.Element nodes
		"""
		err = []

		if self.debug:
			print "#STRUCT: %s" % struct1.get("name")

		# get a list of field names (with anynomous as well)
		fs1 = map(lambda f: f.get("name") if f.get("name") != ""
			else self.constructTypeQualifiedName(f), struct1)
		fs2 = map(lambda f: f.get("name") if f.get("name") != ""
			else self.constructTypeQualifiedName(f), struct2)

		index1, index2 = 0, 0
		l1, l2 = len(struct1), len(struct2)

		if l1 != l2:
			err.append("struct %s has different number of"
				" fields" % struct1.get("name"))

		while index1 < l1 and index2 < l2:

			name1 = fs1[index1]
			name2 = fs2[index2]

			if name1 != name2:
				err.append("fields are not in the same order")
				break

			index1 += 1
			index2 += 1

		s1_dict, s2_dict = {}, {}
		for node in struct1:
			name = node.get("name")
			if name == "":
				name = self.constructTypeQualifiedName(node)

			s1_dict[name] = node

		for node in struct2:
			name = node.get("name")
			if name == "":
				name = self.constructTypeQualifiedName(node)

			s2_dict[name] = node

		# check individual fields
		fs1 = sorted(fs1)
		fs2 = sorted(fs2)
		while index1 < l1 and index2 < l2:
			# check types
			name1 = fs1[index1]
			name2 = fs2[index2]
			if name1 == name2:
				index1 += 1
				index2 += 1
				e = self.compareTypes(s1_dict[name1],
					s2_dict[name2])
				if e != []:
					err += e
			else:
				if name1 < name2:
					index1 += 1
					err.append("%s field is missing" %
						name1)
				else:
					index2 += 1
					err.append("new '%s' field detected" %
						name2)

		# some fields not checked?
		while index1 < l1:
			err.append("field '%s' removed" % fs1[index1])
			index1 += 1

		while index2 < l2:
			err.append("new field '%s' detected" % fs2[index2])
			index2 += 1

		return err

def compareFunctions(funcs1, funcs2):

	# get types names
	funcs1_set = set(map(lambda x: x.get("name"), funcs1[:]))
	funcs2_set = set(map(lambda x: x.get("name"), funcs2[:]))

	new_funcs = list(funcs2_set - funcs1_set)
	rem_funcs = list(funcs1_set - funcs2_set)
	com_funcs = list(funcs1_set & funcs2_set)

	#print new_funcs
	#print com_funcs

def compareTypes(type1, type2):

	# get types names
	type1_set = set(map(lambda x: x.get("name"), type1[:]))
	type2_set = set(map(lambda x: x.get("name"), type2[:]))

	new_types = list(type2_set - type1_set)
	rem_types = list(type1_set - type2_set)
	com_types = list(type1_set & type2_set)

	if new_types != []:
		print "New types: " + ", ".join(new_types)

	if rem_types != []:
		print "Removed types: " + ", ".join(rem_types)

	types1_dir = {}
	types2_dir = {}
	for type in type1:
		if type.get("name") in com_types:
			types1_dir[type.get("name")] = type

	for type in type2:
		if type.get("name") in com_types:
			types2_dir[type.get("name")] = type

	for type in com_types:
		#print types1_dir[type].get("name")
		err = CompareTypes().compareTypes(types1_dir[type], types2_dir[type])
		if err != []:
			print "ERR:\n" + "\n".join(err)

	return

def comparePackages(pkg1, pkg2):
	types1 = None
	funcs1 = None
	names1 = None

	types2 = None
	funcs2 = None
	names2 = None

	for elm in pkg1:
		if elm.tag == "types":
			types1 = elm
		elif elm.tag == "functions":
			funcs1 = elm
		elif elm.tag == "names":
			names1 = elm

	for elm in pkg2:
		if elm.tag == "types":
			types2 = elm
		elif elm.tag == "functions":
			funcs2 = elm
		elif elm.tag == "names":
			names2 = elm

	# check names
	compareNames(names1, names2)

	# check types
	compareTypes(types1, types2)

	# check funcs
	compareFunctions(types1, types2)


if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-e] [-d] DIR1 DIR2")

        parser.add_option_group( optparse.OptionGroup(parser, "file", "Xml file with scanned results") )

	parser.add_option(
	    "", "-d", "--detail", dest="detail", action = "store_true", default = False,
	    help = "Display more information about affected branches"
	)

	parser.add_option(
	    "", "-e", "--executable", dest="executables", action = "store_true", default = False,
	    help = "Include executables in summary"
	)

	options, args = parser.parse_args()
	if len(args) != 2:
		print "Missing DIR1 or DIR2"
		exit(1)

	go_dir1 = args[0]
	go_dir2 = args[1]

	# 1) check if all provided import paths are the same
	# 2) check each package for new/removed/changed symbols

	err, ip1, symbols1, ip_used2 = getSymbolsForImportPaths(go_dir1)
	if err != "":
		print "%s: %s" % (go_dir1, err)
		exit(1)

	err, ip2, symbols2, ip_used2 = getSymbolsForImportPaths(go_dir2)
	if err != "":
		print "%s: %s" % (go_dir2, err)
		exit(1)

	ip1_set = set(ip1.keys())
	ip2_set = set(ip2.keys())

	new_ips = list( ip2_set - ip1_set )
	rem_ips = list( ip1_set - ip2_set )
	com_ips = sorted(list( ip1_set & ip2_set ))

	# list new packages
	if new_ips != []:
		print "new symbols: " + str(new_ips)

	# list removed packages
	if new_ips != []:
		print "removed symbols: " + str(rem_ips)

	# compare common packages
	counter = 1
	for pkg in com_ips:
		obj1 = PackageToXml(symbols1[pkg], "%s" % (ip1[pkg]), imports=False)
		if not obj1.getStatus():
			print obj1.getError()

		obj2 = PackageToXml(symbols2[pkg], "%s" % (ip2[pkg]), imports=False)
		if not obj2.getStatus():
			print obj2.getError()

		print pkg
		comparePackages(obj1.getPackage(), obj2.getPackage())
		counter += 1

		#if counter == 5:
		#	break

		print ""

	exit(0)

	for pkg in ip:
		print "Import path: %s" % (ip[pkg])

		obj = PackageToXml(symbols[pkg], "%s" % (ip[pkg]),  imports=False)
		if obj.getStatus():
			print obj#.getError()
		else:
			print obj.getError()


