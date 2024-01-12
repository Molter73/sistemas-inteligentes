#!/bin/sh -e
set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place "src"
isort -m3 -tc "src"
black "src" -l 80
