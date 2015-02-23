package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"strings"
)

func array2JSON(arr []string) (json string) {
	return "[" + strings.Join(arr, ", ") + "]"
}

func map2JSON(def map[string]string) (json string) {
	arr := make([]string, 0)
	for key, value := range def {
		if value == "" {
			value = "''"
		}
		arr = append(arr, "'" + key + "': " + value)
	}
	json = "{" + strings.Join(arr, ", ") + "}"
	return
}

func parseStruct(t *ast.StructType) (types []string) {
	if t.Fields.List != nil {
		for _, f := range t.Fields.List {
			// get type signature
			sig := parseTypes(f.Type, "")
			if sig == "" {
				continue
			}
			//fmt.Println(sig)
			// anonymous field?
			if f.Names == nil {
				types = append(types, "'': " + sig)

			// named fields
			} else {
				for _, name := range f.Names {
					types = append(types, "'" + name.Name + "': " + sig)
				}
			}
		}
	}
	return
}

func parseFunc(decl *ast.FuncDecl) (sig string) {
	recv := getSymbolReceiver(decl.Recv)
	params := getSymbolParams(decl.Type.Params)
	results := getSymbolResults(decl.Type.Results)
	sig = fncSignature2JSON(decl.Name.Name, recv, params, results)
	return
}

// Returns JSON definition of a type (possibly recursive)
func parseTypes(et ast.Expr, name string) (sig string) {
	//fmt.Println(et)
	switch t := et.(type) {
	case *ast.StarExpr:
		//fmt.Print("StarExpr:")
		sig = "{'type': 'pointer', 'def': "
		sig += parseTypes(t.X, "")
		sig += "}"
	case *ast.Ident:
		//fmt.Print("Ident:")
		sig = "{'type': " + t.Name + "}"
	case *ast.SelectorExpr:
		//fmt.Print("Selector:")
		sig = "{'type': 'selector', 'prefix': "
		sig += parseTypes(t.X, "") + ", 'item': " + t.Sel.Name + "}"
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
		tp["value"] = parseTypes(t.Value, "")
		sig = map2JSON(tp)
	case *ast.StructType:
		//fmt.Println("Struct:")
		// {'name': id, 'type': 'struct', 'def': ...}
		tp := make(map[string]string)
		tp["name"] = name
		tp["type"] = "struct"
		tp["def"]  = array2JSON(parseStruct(t))
		sig = map2JSON(tp)
	case *ast.MapType:
		// {'name': id, 'type': 'map', 'keytype': ..., 'valuetype': ...}
		tp := make(map[string]string)
		tp["name"] = name
		tp["type"] = "map"
		tp["keytype"] = parseTypes(t.Key, "")
		tp["valuetype"] = parseTypes(t.Value, "")
		sig = map2JSON(tp)
	case *ast.ArrayType:
		tp := make(map[string]string)
		tp["name"] = name
		if t.Len == nil {
			tp["type"] = "slice"
		} else {
			tp["type"] = "array"
			// http://golang.org/ref/spec#ArrayType
			// it must evaluate to a non-negative constant representable by a value of type int
			//fmt.Println(getArrayLen(t.Len))
			//tp["len"]  = parseTypes(t.Len, "")
		}
		tp["elmtype"] = parseTypes(t.Elt, "")
		sig = map2JSON(tp)
	case *ast.FuncType:
		params := getSymbolParams(t.Params)
		results := getSymbolResults(t.Results)
		tp := make(map[string]string)
		tp["type"] = "func"
		tp["params"] = "[" + strings.Join(params, ", ") + "]"
		tp["results"] = "[" + strings.Join(results, ", ") + "]"
		sig = map2JSON(tp)
	/*case *ast.BasicLit:
		fmt.Println("BasicLit")
		fmt.Println(t.Value)
	case *ast.BinaryExpr:
		fmt.Println(t.X)
		fmt.Println(t.Op)
		fmt.Println(t.Y)
	case *ast.Ellipsis:
		fmt.Println("Ellipsis")
	*/
	default:
		fmt.Println("Error: check for symbol not implemented.")
		fmt.Println(et)
		fmt.Println(t)
		return ""
	}
	return
}


func getSymbolReceiver(fl *ast.FieldList) (types []string) {
	if fl != nil {
		for _, field := range (*fl).List {
			sig := parseTypes(field.Type, "")
			for i := 0; i < len(field.Names); i++ {
				// parameter type
				types = append(types, sig)
			}
		}			
	}
	return
}

func getSymbolParams(fl *ast.FieldList) (types []string) {
	for _, field := range (*fl).List {
		sig := parseTypes(field.Type, "")
		for i := 0; i < len(field.Names); i++ {
			types = append(types, sig)
		}
	}
	return
}

func getSymbolResults(fl *ast.FieldList) (types []string) {
	if fl != nil {
		for _, field := range fl.List {
			sig := parseTypes(field.Type, "")
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

func fncSignature2JSON(name string, recv []string, params []string, returns []string) (json string) {
	json = name + ": {"
	json += "recv: [" + strings.Join(recv, ", ") + "], "
	json += "params: [" + strings.Join(params, ", ") + "], "
	json += "returns: [" + strings.Join(returns, ", ") + "]"
	json += "}"
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

	typeDefs := make([]string, 0)
	funcDefs := make([]string, 0)
	varcons  := make([]string, 0)
	imports  := make([]string, 0)

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
					sig := "{'name': '"
					if d.Name != nil {
						sig += d.Name.Name
					}
					// if d.Name is '', use a basename of the path?
					sig += "', 'path': '" + d.Path.Value + "'"
					imports = append(imports, sig)
				case *ast.ValueSpec:
					for _, name := range d.Names {
						if ast.IsExported(name.Name) {
							varcons = append(varcons, name.Name)
						}
					}
				case *ast.TypeSpec:
					// {'name': id, 'type': 'struct', 'def': ...}
					def := parseTypes(d.Type, d.Name.Name)
					typeDefs = append(typeDefs, def)
				}
			}
		case *ast.FuncDecl:
			if ast.IsExported(decl.Name.Name) {
				json := parseFunc(decl)
				funcDefs = append(funcDefs, json)
			}
		}
	}
	//return
	fmt.Println("")
	fmt.Println("TYPE DEFS:")
	for _, item := range typeDefs {
		fmt.Println(item)
	}
	fmt.Println("")
	fmt.Println("FUNC DEFS:")
	for _, item := range funcDefs {
		fmt.Println(item)
	}
	fmt.Println("")
	fmt.Println("VAR DEFS:")
	fmt.Println(varcons)
	fmt.Println("")
	fmt.Println("IMPORTS DEFS:")
	for _, item := range imports {
		fmt.Println(item)
	}

}
