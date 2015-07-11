from modules.Plugin import Plugins
from modules.Utils import runCommand
import sys

if len(sys.argv) != 4:
	sys.stderr.write("Synopsis: gen_bash_completion.py PKG_NAME PLUGIN_DIR BASH_COMPLETION_DIR\n")
	exit(1)

pkg_name=sys.argv[1]
plugin_dir=sys.argv[2]
bash_completion_dir=sys.argv[3]

plugins = Plugins(plugin_dir)
if not plugins.read():
	sys.stderr.write("\n".join(plugins.getError()))
	exit(1)

cmd_list = plugins.getCommandList()

# for each plugin:
# 1) create a list of available commands in pl_commands variable (the same for all plugins)
# 2) for each command create a COMMAND_opts variable (specific for each command in each plugin)

# in the bash completion script source one by one all pl_name.sh scripts
# and join all $pl_command into one

def format_string(str):
	str = str.replace("-", "_")
	return str

# for each command get its help
options = {}
for pl_name in cmd_list:
	options[pl_name] = {}
	bc_file = "%s/%s_bash_completion" % (plugin_dir, pl_name)
	with open(bc_file, "w") as fd:
		fd.write("#\n")
		fd.write("#  Completion for %s plugin\n" % pl_name)
		fd.write("#\n")
		fd.write("#  List of commands\n")
		fd.write("pl_commands=\"%s\"\n" % " ".join(cmd_list[pl_name]))
	
		for cmd in cmd_list[pl_name]:
			fd.write("#  %s %s\n" % ('gofed', cmd))
			so, _, _ = runCommand("python parseOptions.py %s %s" % (cmd, plugin_dir))
			options[pl_name][cmd] = so.split("\n")[0].split(":")[1]
			if options[pl_name][cmd] == "":
				fd.write("%s_opts=\"#\"\n" % format_string(cmd))
			else:
				fd.write("%s_opts=\"%s\"\n" % (format_string(cmd), options[pl_name][cmd]))

		fd.write("\n")

	print "# %s generated" % pl_name

# generate the main bash completion script
# generate header
fd = sys.stdout
fd.write("#\n")
fd.write("#  Completion for %s:\n" % pkg_name)
fd.write("#\n")

fd.write("# generate completion\n")
fd.write("PLUGIN_DIR=\"%s\"\n" % bash_completion_dir)
fd.write("_%s()\n" % pkg_name)
fd.write("""{
    local cur prev opts
    _init_completion -s || return
    COMPREPLY=()
    opts=""
    for plugin in gofed-base gofed-scan gofed-build; do
        if [ -f "${PLUGIN_DIR}/${plugin}_bash_completion" ]; then
            source ${PLUGIN_DIR}/${plugin}_bash_completion
            opts="$opts"
        fi
    done
""")
fd.write("    case \"${words[1]}\" in\n")

for pl_name in cmd_list:
	for cmd in cmd_list[pl_name]:
		fd.write("        %s)\n" % cmd)
		if options[pl_name][cmd] != "":
			fsc = format_string(cmd)
			fd.write("            if [ \"$%s_opts\" != \"\" ]; then \n" % fsc)
			fd.write("                if [ \"$%s_opts\" == \"#\" ]; then \n" % fsc)
			fd.write("                    return 0\n")
        		fd.write("                fi\n")

			fd.write("                COMPREPLY=( $(compgen -W '%s' -- ${cur}) )\n" % options[pl_name][cmd])
        		fd.write("                return 0\n")
        		fd.write("            fi\n")
        	fd.write("            ;;\n")

fd.write("""
        *)
        ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}
""")
fd.write("complete -F _%s %s\n" % (pkg_name, pkg_name))
