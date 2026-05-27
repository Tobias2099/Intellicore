# PARSEC Full-System Disk Image

This directory is reserved for the full-system PARSEC path described by the
gem5 tutorial. Generated images and packer outputs are ignored by Git.

Use this path when SE-mode binaries are not enough and the benchmark should
run inside a Linux guest with PARSEC installed on a disk image.

The local implementation should keep only scripts and templates here. Do not
commit built `.img`, `.iso`, `.qcow2`, or packer output directories.

