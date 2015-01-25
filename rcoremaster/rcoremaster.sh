#!/bin/bash

export PYTHONPATH="$(dirname $0)/../rcorelib/:${PYTHONPATH}"

$(dirname $0)/rcoremaster.py

exit $?
