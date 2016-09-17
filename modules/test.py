import jinja2
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

def renderTemplate(template_file, template_vars):

	templateLoader = jinja2.FileSystemLoader( searchpath=script_dir )
	templateEnv = jinja2.Environment( loader=templateLoader )
	template = templateEnv.get_template( template_file )
	content = template.render( template_vars )

	print content


import_path_prefix = "github.com/coreos/etcd"
provider_prefix = "github.com/coreos/etcd"
project_signature = {
	"provider": {
		"provider": "github",
		"username": "coreos",
		"project": "etcd"
	},
	"commit": "b7761530e1d5b9f404811d63786df60023a88db9"
}

project_signature = {
	"provider": {
		"provider": "bitbucket",
		"username": "ww",
		"project": "goautoneg",
	},
	"commit": "b7761530e1d5b9f404811d63786df60023a88db9"
}

project_signature = {
	"provider": {
		"provider": "googlecode",
		"username": "",
		"project": "go.net",
	},
	"rev": "b7761530e1d5b9f404811d63786df60023a88db9"
}

renderTemplate("spec.jinja", {
	"with_build": True,
	"import_path_prefix": import_path_prefix,
	"provider_prefix": provider_prefix,
	"project_signature": project_signature,
	"licenses": [{
		"type": "MIT/X11",
		"file": "LICENSE"
	}],
	"rrepo": "net.go",
	"stripped_repo": "net"
})
