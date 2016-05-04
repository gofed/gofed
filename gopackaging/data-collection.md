# Periodic collection of datas

Aim of this document is to cover periodic scan of the distribution.

## Latest distribution snapshot

The distribution snapshot provides a list of all detected (optionaly with custom) golang packages
each with its corresponding latest build (with a list of rpms).
Data from the latest builds are extracted.

Let's run the scan periodically, collect the latest builds so it can be used for analysis.

The first analysis in mind is to check dependency graph to see what golang package are missing.

### Proposal

1) create Jenkins Job that periodically triggers 'gofed scan-distro' and 'gofed scan-deps'.
2) store new data under https://github.com/gofed/data project
3) store logs under https://github.com/gofed/data project

