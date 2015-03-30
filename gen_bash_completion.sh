#!/bin/sh
# 1 - package name
pkg=$1

HELP="apidiff build check-commit check-deps gcpmaster ggi inspect lint scandeps scan-imports scaninfo scansymbols scan-packages wizard"
rm -f tools.options
for cmd in $HELP; do
	python parseOptions.py $cmd >> tools.options
done

##########################

if [ "$pkg" == "" ]; then
	"error: unable to generate bash completion, missing package name"
	exit 1
fi

ops=$(echo $(cat $pkg | grep 'if \[ "$1" ==' | cut -d'=' -f3 | cut -d']' -f1 | sed 's/ *//g' | sed 's/"//g'))


# generate header
echo "#"
echo "#  Completion for $pkg:"
echo "#"
for operation in $ops; do
	echo "#  $pkg $operation"
done
echo ""

# generate completion
cat << EOF
_$pkg()
{
    local cur prev opts
    COMPREPLY=()
    cur="\${COMP_WORDS[COMP_CWORD]}"
    prev="\${COMP_WORDS[COMP_CWORD-1]}"
EOF
echo "    opts=\"$ops\""
echo "    case "\${prev}" in"

for operation in $ops; do
	opts=$(cat tools.options | grep "^$operation:" | cut -d':' -f2)
	if [ "$opts" != "" ]; then
		echo "        $operation)"
		echo "            COMPREPLY=( \$(compgen -W '$opts') )"
	        echo "            return 0"
	        echo "            ;;"
	fi
done

cat << EOF
        *)
        ;;
    esac

    COMPREPLY=( \$(compgen -W "\${opts}" -- \${cur}) )
}
complete -F _$pkg $pkg
EOF

rm -f tools.options
