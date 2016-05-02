import jinja2
from gofed_lib.utils import getScriptDir
import os

script_dir = getScriptDir(__file__)

def renderTemplate(template_file, template_vars, file):

	templateLoader = jinja2.FileSystemLoader( searchpath=script_dir )
	templateEnv = jinja2.Environment( loader=templateLoader )
	template = templateEnv.get_template( template_file )
	content = template.render( template_vars )

	with open(file, "w") as f:
		f.write(content)

rootdir = os.path.dirname(script_dir)

print "rendering gofed-resources-client.service"
renderTemplate(
	"templates/gofed-resources-client.jinja", {
	"envs": "GOFED_DEVEL=1 PYTHONPATH=%s/third_party" % rootdir,
	"resourceclientdaemon": "%s/third_party/gofed_infra/system/daemons/resourceclientdaemon.py" % rootdir},
	"%s/daemons/gofed-resources-client.service" % script_dir
	)

print "rendering gofed-resources-provider.service"
renderTemplate(
	"templates/gofed-resources-provider.jinja", {
	"envs": "GOFED_DEVEL=1 PYTHONPATH=%s/third_party" % rootdir,
	"resourceproviderdaemon": "%s/third_party/gofed_infra/system/daemons/resourceproviderdaemon.py" % rootdir},
	"%s/daemons/gofed-resources-provider.service" % script_dir
)

print  "rendering third_party/gofed_infra/system/config/infra.conf"
renderTemplate(
	"templates/infra.jinja", {
	"resource_client_dir": "%s/working_directory/resource_client" % rootdir,
	"simplefilestorage": "%s/working_directory/simplefilestorage" % rootdir},
	"%s/third_party/gofed_infra/system/config/infra.conf" % rootdir
)

print "third_party/gofed_resources/proposal/config/resources.conf"
renderTemplate(
	"templates/resources.jinja", {
	"resource_provider_dir": "%s/working_directory/resource_provider" % rootdir,
	"storage_dir": "%s/working_directory/storage" % rootdir},
	"%s/third_party/gofed_resources/proposal/config/resources.conf" % rootdir
)

