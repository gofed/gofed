# Scanning distro within a container

## Steps

1. build the docker container: ``make``
2. run the container with mounted keytab file and ssh private key

e.g.
```
docker run -u gofed \
        -v /path/to/key/tab/keytab:/etc/username.keytab \
        -v /path/to/private/ssh/key:/home/gofed/.ssh/id_rsa \
        -it gofed/gofed-scan-distro:v0.0.1 /home/gofed/gofed/run-scan.sh ${user} ${target}
```

* the keytab file is needed to authenticate via kerberos to access koji rest api
* the private ssh key is needed to push to a gofed/data repository via ssh
