# Commands [DRAFT]

## Default command

By default, gofed command is run inside a host system.

## Docker based command (partially implemented)

When running `./cmd/gofed-docker`, command is run inside a Docker container.
In order to run to command, user input must be translated into Docker based command.
If an option or argument points to host path, the path must be mounted into the container.
It is a responsibility of a gofed developer to prepare all necassary data, e.g.:

* base image
* mapping of user input into Docker command
* other necassary conversions

Docker itself expects a run command.

## Kubernetes based command (not yet implemented)

When running `./cmd/gofed-kube`, command is run as a job inside a Kubernetes cluster.
In order to run the command, user input must be translated into job description.
If an option or argument points to hostn path, the path must be uploaded to a location available from withing the cluster.
It is a responsibility of a gofed developer to prepare all necassary data, e.g.:

* base image
* mapping of user input into Kubernetes job specification
* mechanism of uploading host path to a network location avaiable from withing a Kubernetes cluster
* other necassary conversions

Kubernetes itself expects a job specification (or specification of different object where reasonable).

# Target system (not yet implemented)

Each target system (Docker, Kubernetes, Jenkins, Vagrant, etc.) has its own input definition it expects.
Thus, it is up to a gofed developer to provide such definition.
As a given definition is gofed (or project) specific, it is stored in the gofed (or project) itself.
Later, new repository can be distinguished to store all the definitions such as:

* gofed-docker
* gofed-kube
* gofed-jenkins
* gofed-vagrant

Or, all the definitions (translation and definition generator code) can be stored under common repository such as `gofed-deploy`.
With separate directory for each target system.

As each command is user input dependent, every definition must be made parametric in general.
