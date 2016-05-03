# What branches are under Go pressure. Did we forget about epel7?

Since F17, golang started to get attention in Fedora distribution.
Long way was travelled since with currently activelly maintaining f22+ and el6 branches.
The number of Go projects packaged in Fedora grown to more than 250 packages.
The current effort is to keep in shape all activelly managed branches including el6.
As the Golang language is spreading across new architectures, new challenges pop up.
With 250 packages in distribution we have a free source of Go source code to play with
and run various analysis on. To see how the Golang compiler is doing on secondary architectures.
To see how new OSes accept new versions of projects written in Go.
Or be a witness to dynamic changes in Go community.

Currently, we have Fedora, RHEL and CentOS in our disposal.
It has been quite a ride to watch how all the projects evolve,
what challenges they generate, questions they rise.
With the infrastructure we have, with the variability of OSes and architectures,
it is a perfect time to experiment and push the community further.

A lot of work has been already done.
I would like to continue with that effort
and extend the currently maintained branches to epel7.
It is a great opportunity to see how the Go actually works for all the projects on RHEL.
The more projects we can test and run, the higher chance to discover bootlenecks we have.
At the same time all the projects can be tested with newer version of Go compiler
even before it gets into RHEL and fix the critical issues in advance.

There are already some Go packages built in RHEL7.
It has been one of the reasons in the air why it is not efortfull to maintain Go in epel7.
Once a package gets into RHEL7, it has to be retired from epel7.
Thus, it would generate an amount of work that would be thrown away.
Still, it makes sense to keep both Fedora and RHEL in sync on a level of Go packaging.

CentOS has its own collection of Go packages already.
Another opportunity to test and run and see how everything works.

For quite some time I have been working on gofed tool [1].
At the current state it is strongly oriented on packaging.
With its help I am able to update and build Go packages on all affected branches
with minimal effort. For that, I would like to extend the coverage to both epel7 and centos7.
There are already BZs opened for epel7 packaging which should not be ignored.

I would like to start with epel7. As there are just few Go packages with epel7 branch,
it will require some time spent on generated requests for new branch and (re)building
entire Go part of epel7. The primary aim is to backport devel subset of each Go project.
It does not mean there will be no rpms with binaries. First, I would like to sync epel7 with
Fedora rawhide. Then, start fixing all projects that fail to build.
Any help on collection requirements for it is appreciated.
There will be some collisions with Go packages already in RHEL7 so one needs to be carefull.

Steps I suggest:
1) make a list of all Go packages that are missing epel7 branch and does not conflict with RHEL7
2) request for missing epel7 branches (at least 200)
3) backport all affected Go packages from Fedora rawhide to epel7
4) start fixing all failing tests and reporting issues to upstream

There are other tasks that needs to be done or initiated:
- start running unit-test in all Go packages periodically,
- scan the distribution for broken or breaking packages
- provider better feedback to developers
- finish the Go packaging guidelines

The current emphasis of the gofed tool is extend the concentration on ecosystem analysis.
I have already implemented scans of the latest rpms in distribution.
So the tool is already capable of collection basic information about Go projects we have.
From the collected data, dependency graph among rpms can be constructed.
And other analysis that are already there. Another step is "just" to start
running all the scans and analysis periodically and collect the current state of the ecosystem.

I would like to thank to all who have contributed and help making the Go ecosystem better.
It is a lot of effort, a lot of free time spent and dreamless nights.
Let's continue in the great work we have done so far.

[1] https://github.com/gofed/gofed

Sent to Fedora ML: https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/IQK33J636MVMIDM6VXGHK367DGGRRKU7/

