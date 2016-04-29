find . -iname "*.pyc"
rm -rf $(find . -iname "*.pyc")

find . -iname "__pycache__"
rm -rf $(find . -iname "__pycache__")
