#!/bin/sh

# 1 - package name
pkg=$1

if [ "$pkg" == "" ]; then
	"error: unable to generate bash completion, missing package name"
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
	echo "        $operation)"
	echo "            COMPREPLY=( \$(compgen -f \${cur}) )"
        echo "            return 0"
        echo "            ;;"
done

cat << EOF
        *)
        ;;
    esac

    COMPREPLY=( \$(compgen -W "\${opts}" -- \${cur}) )
}
complete -F _$pkg $pkg
EOF
