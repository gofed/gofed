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

			print "NAME: " + ident1.get("name")

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

		prefix.item

		Two selectors are identical if they have the same
		prefix (prefix tag) and item (item tag)
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

		print err
		return err

	def compareSlices(self, slice1, slice2):
		err = []

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

		for node in method2:
			if node.tag == "paramsList":
				params2 = node
			elif node.tag == "resultsList":
				results2 = node

		# check parameters
		if len(params1) != len(params2):
			err.append("Methods differs in parameter count")
			return err

		for i in range(0, len(params1)):
			self.compareTypes(params1[i], params2[i])
			print params1[i].tag
			print params2[i].tag

	def compareInterfaces(self, interface1, interface2):
		print "interface %s" % interface1.get("name")

		m1_set = set(map(lambda m: m.get("name"), interface1[:]))
		m2_set = set(map(lambda m: m.get("name"), interface2[:]))

		new_ms = list(m2_set - m1_set)
		rem_ms = list(m1_set - m2_set)
		com_ms = list(m1_set & m2_set)


		if new_ms != []:
			print "New methods: " + ", ".join(new_ms)

		if rem_ms != []:
			print "Removed methods: " + ", ".join(rem_ms)

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
			self.compareMethods(m1s_dir[method_name],
				m2s_dir[method_name])

			print method_name


		#for method in type1:
		#	print method.tag
			#self.compareMethods(

		exit(0)

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
		elif type == "struct":
			return self.compareStructs(type1, type2)
		else:
			print "%s type not implemented yet" % type
			exit(0)
			return []

		return []

	def constructTypeQualifiedName(self, type):
		"""
		For given type construct its full qualified name.

		
		"""
		t = type.get("type")
		if t == "ident":
			print "FQN: %s" % type.get("def")
			return type.get("def")
		elif t == "pointer":
			return self.constructTypeQualifiedName(type[0])
		else:
			print "FQN type not implemented: %s" % t
			exit(0)
			return ""

	# struct must have the same number of fields and their corresponding names
	def compareStructs(self, struct1, struct2):
		"""
		Struct is defined by its fields.
		Field consists of a name (name attribute) and type definition.

		Order of fields is not important (not implemented yet).
		Only name:type are.

		For anonymous field an unqualified type name is taken.

		struct1, struct2: etree.Element nodes
		"""
		err = []
		# check fields
		for field in struct1:
			print self.constructTypeQualifiedName(field)
		#print map(lambda i: i, struct1[:])
		#f1_set = set(struct1[:])
		#print f1_set

		if len(struct1) != len(struct2):
			err.append("Error: structs have different number of arguments")
			return err

		# check individual fields
		# maybe order of fields is not important?
		print "Struct's name: %s" % struct1.get("name")
		for i in range(0, len(struct1)):

			if struct1[i].get("name") != struct2[i].get("name"):
				err.append("Error: %s-th field differs: %s != %s" % (i, struct1[i].get("name"), struct2[i].get("name")))
				return err

			err = self.compareTypes(struct1[i], struct2[i])
			if err:
				print err

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
		CompareTypes().compareTypes(types1_dir[type], types2_dir[type])


		continue
		print types1_dir[type].get("type")
		print types2_dir[type].get("type")

		if types1_dir[type].get("type") != types2_dir[type].get("type"):
			print "%s's type is diffrent from %s's type" % (types1_dir[type].get("name"), types2_dir[type].get("name"))
			continue

		t = types1_dir[type].get("type")
		if t == "struct":
			CompareTypes().compareStructs(types1_dir[type], types2_dir[type])

		print ""

	return

	#compareNodes(type1, type2)

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

	#print pkg2

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

	err, ip2, symbols2, ip_used2 = getSymbolsForImportPaths(go_dir1)
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
	for pkg in com_ips:
		obj1 = PackageToXml(symbols1[pkg], "%s" % (ip1[pkg]), imports=False)
		if not obj1.getStatus():
			print obj1.getError()

		obj2 = PackageToXml(symbols2[pkg], "%s" % (ip2[pkg]), imports=False)
		if not obj2.getStatus():
			print obj2.getError()

		print pkg
		comparePackages(obj1.getPackage(), obj2.getPackage())
		break


	exit(0)

	for pkg in ip:
		print "Import path: %s" % (ip[pkg])

		obj = PackageToXml(symbols[pkg], "%s" % (ip[pkg]),  imports=False)
		if obj.getStatus():
			print obj#.getError()
		else:
			print obj.getError()


