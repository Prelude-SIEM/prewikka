#!/bin/sh

for file in `find . -name '*.tmpl'`; do
    cheetah-compile --nobackup $file
done
