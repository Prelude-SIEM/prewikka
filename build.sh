#!/bin/sh

for file in `find . -name '*.tmpl'`; do
    basename=`echo $file | sed s/.tmpl//`
    if [ ${basename}.tmpl -nt ${basename}.py ]; then
	cheetah-compile --nobackup $file
    fi
done
