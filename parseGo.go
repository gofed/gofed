package main

/*
# TODO
#   - for a given file (*.go source code), list symbols (variables, types,
#     fields, interfaces, functions, ...), that are used and exported
#   - do the same for a given directory
#   - do the same for an entire project (entire directory hiearchy)

###############################################################################
# Based on a definition of exported identifiers [1]                           #
#                                                                             #
# An identifier may be exported to permit access to it from another package.  #
# An identifier is exported if both:                                          #
# 1) the first character of the identifier's name is a Unicode upper case     #
#    letter (Unicode class "Lu"); and                                         #
# 2) the identifier is declared in the package block or it is a field name or #
#    method name.                                                             #
#                                                                             #
# All other identifiers are not exported.                                     #
###############################################################################
# What is identifier? Or what it can be?
# It can be constant [3], 
#
# What is a field name?
# Struct is composed of fields
#
# What is a method name?
# It is a function with a receiver (function of a struct)
#
# Sources:
# [1]	http://golang.org/ref/spec#Declarations_and_scope
# [2]	http://golang.org/ref/spec#Struct_types
# [3]	http://golang.org/ref/spec#Constant_declarations
# [4]	http://golang.org/ref/spec#Type_declarations
# [5]	http://golang.org/ref/spec#Function_declarations
# [6]	http://golang.org/ref/spec#Signature
# [7]	http://golang.org/pkg/go/ast/#FuncType
###############################################################################
# Steps:
# 1: parse out all definitions of constants (name and value, value to trace
#    its changes) [3]
# 2: parse out all definitions of types (name and its value,
#    can be recursive) [4]
#

# Function declaration [5]
# FunctionDecl = "func" FunctionName ( Function | Signature ) .
# FunctionName = identifier .
# Function     = Signature FunctionBody .
# FunctionBody = Block .
#
# FunctionBody is not important. Only Signature is [6].
# Watch out variadic parameter (0-n parametres as ... instead of name)
#
# Function signature in a form:
# "fnc": func_name type type type
#
# As variable definition does not have to specify type, it is complicated
# to determine the type from its value. The value can consist of function
# calls possibly from different packages. So only its name is extracted.
#
###############################################################################
# struct_json: {'name': "...", 'type': "struct", }
#
# id base_type		=>	{'name': id, 'type': base_type}
# id struct {...}	=>	{'name': id, 'type': 'struct', 'def': ...}
#
# GoSymbols = {'consts': [...],'vars': [...],'types': TypesList, 'funcs': [...]
# TypesList = [{"name": Ident, "type": Type[, "def": TypeDef]},{},...,{}]
# Type = BaseType | "struct" | ...
# ### For compounded types
# TypeDef = 
#
###############################################################################
# PACKAGE NAME AND IMPORT PATH                                                #
###############################################################################
# Package names
# - Go's convention is that the package name is the last element of the import
#   path: the package imported as "crypto/rot13" should be named rot13. [1]
#
# Import paths
# - An import path (see 'go help packages') denotes a package stored in the
# local file system. In general, an import path denotes either a standard
# package (such as "unicode/utf8") or a package found in one of the work spaces
# (see 'go help gopath'). [2]
#
# Relative path
# An import path beginning with ./ or ../ is called a relative path. [3]
#
# Import for side effect
# - import _ "net/http/pprof"
# - used only for a side effect
#
# If the PackageName is omitted, it defaults to the identifier specified in the
# package clause of the imported package. [4]
# If an explicit period (.) appears instead of a name, all the package's
# exported identifiers declared in that package's package block will be
# declared in the importing source file's file block and must be accessed
# without a qualifier. [4]
# import   "lib/math"    ->     math.Sin
# import m "lib/math"    ->     m.Sin
# import . "lib/math"    ->     Sin
#
# Another convention is that the package name is the base name of its
# source directory. [5]
#
# <siXy> you can have multiple files in a directory, but they need to be
# all the same package.
# <smw> jchaloup, directory and package are 1:1
# <smw> a package is in only one folder and a folder only contains one package
#
# Directory and file names that begin with "." or "_" are ignored by the
# go tool, as are directories named "testdata".
#
# [1] https://golang.org/doc/code.html#PackageNames
# [2] https://golang.org/cmd/go/#hdr-Import_path_syntax
# [3] https://golang.org/cmd/go/#hdr-Remote_import_paths
# [4] http://golang.org/ref/spec#Import_declarations
# [5] http://golang.org/doc/effective_go.html#names
*/

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"strings"
	"path"
)

// array2JSON transforms an array of strings into JSON.
func array2JSON(arr []string) (json string) {
	var arr_vals []string
	for _, value := range arr {
		value = strings.TrimSpace(value)
		if !strings.HasPrefix(value, "[") &&
                   !strings.HasPrefix(value, "{") {
			value = "\"" + value + "\""
		}
		arr_vals = append(arr_vals, value)
	}
	return "[" + strings.Join(arr_vals, ", ") + "]"
}

// map2JSON transforms a map of strings into JSON.
func map2JSON(def map[string]string) (json string) {
	arr := make([]string, 0)
	for key, value := range def {
		field := "\"" + key + "\": "
		value = strings.TrimSpace(value)
		if strings.HasPrefix(value, "[") || strings.HasPrefix(value, "{") {
			field += value
		} else {
			field += "\"" + value + "\""
		}
		arr = append(arr, field)

	}
	json = "{" + strings.Join(arr, ", ") + "}"
	return
}

// parseStruct returns all fields of struct.
// It returns an array of fields.
func parseStruct(t *ast.StructType) (types []string, err int) {
	if t.Fields.List != nil {
		var sig string
		for _, f := range t.Fields.List {
			// get type signature
			sig, err = parseTypes(f.Type, "")
			if err != 0 {
				return
			}
			if sig == "" {
				continue
			}
			//fmt.Println(sig)
			// anonymous field?
			if f.Names == nil {
				df := make(map[string]string)
				df["name"] = ""
				df["def"]  = sig
				types = append(types, map2JSON(df))
			// named fields
			} else {
				for _, name := range f.Names {
					df := make(map[string]string)
					df["name"] = name.Name
					df["def"]  = sig
					types = append(types, map2JSON(df))
				}
			}
		}
	}
	return
}

// parseFunc transforms a function declaration into a JSON.
func parseFunc(decl *ast.FuncDecl) (sig string, err int) {
	var recv, params, results []string

	recv, err = getSymbolReceiver(decl.Recv)
	if err != 0 {
		return
	}

	params, err = getSymbolParams(decl.Type.Params)
	if err != 0 {
		return
	}

	results, err = getSymbolResults(decl.Type.Results)
	if err != 0 {
		return
	}

	sig = fncSignature2JSON(decl.Name.Name, recv, params, results)
	return
}

func parseInterface(t * ast.InterfaceType) (sig []string, err int) {
	var def string
	for _, m := range t.Methods.List {
		for _, name := range m.Names {
			tp := make(map[string]string)
			tp["type"] = "method"
			tp["name"] = name.Name

			def, err = parseTypes(m.Type, name.Name)
			if err != 0 {
				return
			}

			tp["def"] = def
			sig = append(sig, map2JSON(tp))
		}
	}
	return
}

// parseTypes returns JSON definition of a type (possibly recursive).
func parseTypes(et ast.Expr, name string) (sig string, err int) {
	err = 0
	var d string
	var s []string
	switch t := et.(type) {
	case *ast.StarExpr:
		sig = "{\"type\": \"pointer\", \"def\": "
		d, err = parseTypes(t.X, "")
		if err != 0 {
			return
		}
		sig += d
		sig += "}"
	case *ast.Ident:
		sig = "{\"type\": \"" + t.Name + "\"}"
	case *ast.SelectorExpr:
		sig = "{\"type\": \"selector\", \"prefix\": "
		d, err = parseTypes(t.X, "")
		if err != 0 {
			return
		}
		sig += d + ", \"item\": \"" + t.Sel.Name + "\"}"
	case *ast.ChanType:
		// {'type': 'channel', 'dir': ..., 'value': ...}
		tp := make(map[string]string)
		tp["type"] = "chan"
		switch t.Dir {
		case ast.SEND:
			tp["dir"] = "1"
		case ast.RECV:
			tp["dir"] = "2"
		default:
			tp["dir"] = "3"
		}
		d, err = parseTypes(t.Value, "")
		if err != 0 {
			return
		}
		tp["value"] = d
		sig = map2JSON(tp)
	case *ast.StructType:
		// {'name': id, 'type': 'struct', 'def': ...}
		tp := make(map[string]string)
		tp["name"] = name
		tp["type"] = "struct"
		s, err = parseStruct(t)
		if err != 0 {
			return
		}
		tp["def"] = array2JSON(s)
		sig = map2JSON(tp)
	case *ast.MapType:
		// {'name': id, 'type': 'map', 'keytype': ..., 'valuetype': ...}
		tp := make(map[string]string)
		tp["name"] = name
		tp["type"] = "map"
		d, err = parseTypes(t.Key, "")
		if err != 0 {
			return
		}
		tp["keytype"] = d
		d, err = parseTypes(t.Value, "")
		if err != 0 {
			return
		}
		tp["valuetype"] = d
		sig = map2JSON(tp)
	case *ast.ArrayType:
		tp := make(map[string]string)
		tp["name"] = name
		if t.Len == nil {
			tp["type"] = "slice"
		} else {
			tp["type"] = "array"
			// http://golang.org/ref/spec#ArrayType
			// it must evaluate to a non-negative constant
			// representable by a value of type int
			//fmt.Println(getArrayLen(t.Len))
			//tp["len"]  = parseTypes(t.Len, "")
		}
		d, err = parseTypes(t.Elt, "")
		if err != 0 {
			return
		}
		tp["elmtype"] = d
		sig = map2JSON(tp)
	case *ast.FuncType:
		var params, results []string
		// parameter name is not important, only its type is
		params, err = getSymbolParams(t.Params)
		if err != 0 {
			return
		}
		results, err = getSymbolResults(t.Results)
		if err != 0 {
			return
		}
		tp := make(map[string]string)
		tp["type"] = "func"
		tp["params"] = "[" + strings.Join(params, ", ") + "]"
		tp["results"] = "[" + strings.Join(results, ", ") + "]"
		sig = map2JSON(tp)
	case *ast.InterfaceType:
		s, err = parseInterface(t)
		if err != 0 {
			return
		}

		tp := make(map[string]string)
		tp["type"] = "interface"
		tp["name"] = name
		tp["def"]  = array2JSON(s)
		sig = map2JSON(tp)
	case *ast.Ellipsis:
		d, err = parseTypes(t.Elt, "")
		if err != 0 {
			return
		}

		tp := make(map[string]string)
		tp["type"] = "ellipsis"
		tp["elt"]  = d
		sig = map2JSON(tp)
	/*case *ast.BasicLit:
		fmt.Println("BasicLit")
		fmt.Println(t.Value)
	case *ast.BinaryExpr:
		fmt.Println(t.X)
		fmt.Println(t.Op)
		fmt.Println(t.Y)
	*/
	default:
		err = 1
		fmt.Println("Error: check for symbol not implemented.")
		fmt.Println(et)
		fmt.Println(t)
	}
	return
}

// getSymbolReceiver returns receiver of a function as a list of types.
func getSymbolReceiver(fl *ast.FieldList) (types []string, err int) {
	if fl != nil {
		var sig string
		for _, field := range (*fl).List {
			sig, err = parseTypes(field.Type, "")
			if err != 0 {
				return
			}
			for i := 0; i < len(field.Names); i++ {
				// parameter type
				types = append(types, sig)
			}
		}			
	}
	return
}

// getSymbolParams returns params of a function as a list of types.
func getSymbolParams(fl *ast.FieldList) (types []string, err int) {
	var sig string
	for _, field := range (*fl).List {
		sig, err = parseTypes(field.Type, "")
		if err != 0 {
			return
		}

		if field.Names == nil {
			types = append(types, sig)
		} else {
			for i := 0; i < len(field.Names); i++ {
				types = append(types, sig)
			}
		}
	}
	return
}

// getSymbolResults returns results type of a function as a list of types.
func getSymbolResults(fl *ast.FieldList) (types []string, err int) {
	if fl != nil {
		var sig string
		for _, field := range fl.List {
			sig, err = parseTypes(field.Type, "")
			if err != 0 {
				return
			}
			rt := len(field.Names)
			for i := 0; i < rt; i++ {
				types = append(types, sig)
			}
			if rt == 0 && sig != "" {
				types = append(types, sig)
			}
		}
	}
	return
}

// fncSignature2JSON return function signature as a JSON.
func fncSignature2JSON(name string, recv []string, params []string,
     returns []string) (json string) {
	json = "{\"name\": \"" + name + "\", \"def\": {"
	json += "\"recv\": [" + strings.Join(recv, ", ") + "], "
	json += "\"params\": [" + strings.Join(params, ", ") + "], "
	json += "\"returns\": [" + strings.Join(returns, ", ") + "]"
	json += "}}"
	return
}

type Symbols struct {
	pkgName string
	typeDefs []string
	funcDefs []string
	varcons  []string
	imports  []string
}

func (symbols * Symbols) ToJSON() (json string) {
	dict := make(map[string]string)
	dict["pkgname"] = symbols.pkgName
	dict["types"] = array2JSON(symbols.typeDefs)
	dict["funcs"] = array2JSON(symbols.funcDefs)
	dict["vars"]  = array2JSON(symbols.varcons)
	dict["imports"] = array2JSON(symbols.imports)
	return map2JSON(dict)
}

func (symbols * Symbols) setPackageName(name string) {
	symbols.pkgName = name
}

func (symbols * Symbols) AddImport(d *ast.ImportSpec) {
	sig := "{\"name\": "
	if d.Name != nil {
		sig += "\"" + d.Name.Name + "\""
	// If the PackageName is omitted, it defaults to the identifier
	// specified in the package clause of the imported package, .i.e.
	// use a basename of the path
	} else if (d.Path.Value != "") {
		sig += "\"" + strings.Replace(path.Base(d.Path.Value), "\"", "", -1) + "\""
	}
	sig += ", \"path\": " + d.Path.Value + "}"
	symbols.imports = append(symbols.imports, sig)
}

func (symbols * Symbols) AddVar(d *ast.ValueSpec) {
	for _, name := range d.Names {
		if ast.IsExported(name.Name) {
			symbols.varcons = append(symbols.varcons, name.Name)
		}
	}
}

func (symbols * Symbols) AddTypes(d *ast.TypeSpec) (err int) {
	// {'name': id, 'type': 'struct', 'def': ...}
	var def string
	def, err = parseTypes(d.Type, d.Name.Name)
	if err != 0 {
		return
	}
	if _, ok := d.Type.(*ast.Ident); ok {
		df := make(map[string]string)
		df["name"] = d.Name.Name
		df["type"] = "ident"
		df["def"]  = def
		symbols.typeDefs = append(symbols.typeDefs, map2JSON(df))
		return
	}
	if _, ok := d.Type.(*ast.StarExpr); ok {
		df := make(map[string]string)
		df["name"] = d.Name.Name
		df["type"] = "pointer"
		df["def"]  = def
		symbols.typeDefs = append(symbols.typeDefs, map2JSON(df))
		return
	}
	if _, ok := d.Type.(*ast.SelectorExpr); ok {
		df := make(map[string]string)
		df["name"] = d.Name.Name
		df["type"] = "selector"
		df["def"]  = def
		symbols.typeDefs = append(symbols.typeDefs, map2JSON(df))
		return
	}
	if _, ok := d.Type.(*ast.ChanType); ok {
		df := make(map[string]string)
		df["name"] = d.Name.Name
		df["type"] = "channel"
		df["def"]  = def
		symbols.typeDefs = append(symbols.typeDefs, map2JSON(df))
		return
	}

	symbols.typeDefs = append(symbols.typeDefs, def)
	return
}

func (symbols * Symbols) AddFunc(decl *ast.FuncDecl) (err int) {
	if ast.IsExported(decl.Name.Name) {
		var json string
		json, err = parseFunc(decl)
		if err != 0 {
			return
		}

		symbols.funcDefs = append(symbols.funcDefs, json)
	}
	return
}

func main() {
	fset := token.NewFileSet() // positions are relative to fset

	if len(os.Args) < 2 {
		fmt.Println("prog GOFILE")
		return
	}

	// Parse the file containing this very example
	// but stop after processing the imports.
	f, err := parser.ParseFile(fset, os.Args[1], nil, 0)
	if err != nil {
		fmt.Println(err)
		return
	}

	symbols := new(Symbols)

	symbols.setPackageName(f.Name.Name)

	// Print the imports from the file's AST.
	for _, d := range f.Decls {
		// accessing dynamic_value := interface_variable.(typename)
		switch decl := d.(type) {
		case *ast.GenDecl:
			//fmt.Println(decl.Tok)
			for _, spec := range decl.Specs {
				//fmt.Println(spec)
				switch d := spec.(type) {
				case *ast.ImportSpec:
					symbols.AddImport(d)
				case *ast.ValueSpec:
					symbols.AddVar(d)
				case *ast.TypeSpec:
					err := symbols.AddTypes(d)
					if err != 0 {
						os.Exit(err)
					}
				}
			}
		case *ast.FuncDecl:
			symbols.AddFunc(decl)
		}
	}
	fmt.Println(symbols.ToJSON())
	os.Exit(0)
}
