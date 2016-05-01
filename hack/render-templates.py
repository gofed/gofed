import jinja2
from gofed_lib.utils import getScriptDir
import os

script_dir = getScriptDir(__file__)

def renderTemplate(template_file, template_vars):

	templateLoader = jinja2.FileSystemLoader( searchpath=script_dir )
	templateEnv = jinja2.Environment( loader=templateLoader )
	template = templateEnv.get_template( template_file )
	return template.render( template_vars )

rootdir = os.path.dirname(script_dir)

# render gofed-resources-client.service

content = renderTemplate(
	"templates/gofed-resources-client.jinja", {
	"pythonpath": "%s/third_party" % rootdir,
	"resourceclientdaemon": "%s/third_party/gofed_infra/system/daemons/resourceclientdaemon.py" % rootdir
	})

with open("%s/daemons/gofed-resources-client.service" % script_dir, "w") as f:
	f.write(content)

# render gofed-resources-provider.service

content = renderTemplate(
	"templates/gofed-resources-provider.jinja", {
	"pythonpath": "%s/third_party" % rootdir,
	"resourceproviderdaemon": "%s/third_party/gofed_infra/system/daemons/resourceproviderdaemon.py" % rootdir
	})

with open("%s/daemons/gofed-resources-provider.service" % script_dir, "w") as f:
	f.write(content)

