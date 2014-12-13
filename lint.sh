#!/usr/bin/env bash

# all errors or warnings, except:
#  W0142 star-args
#  W0212 protected-access
#  W0221 arguments-differ
#  W0511 fixme
#  W0611 unused-import (due to Python version differences)
#  F0401 import-error (due to Python version differences)
#  W0704 pointless-except (due to Python version differences)

enable_always="E0001,E0011,E0012,E0100,E0101,E0102,E0103,E0104,E0105,E0106,E0107,E0108,E0202,E0203,E0211,E0213,E0221,E0222,E0235,E0501,E0502,E0503,E0601,E0602,E0603,E0604,E0611,E0701,E0702,E0710,E0711,E0712,E1001,E1002,E1003,E1004,E1101,E1103,E1111,E1120,E1121,E1122,E1123,E1124,E1125,E1200,E1201,E1205,E1206,E1300,E1301,E1302,E1303,E1304,E1305,E1306,E1310,F0001,F0002,F0003,F0004,F0010,F0202,F0220,F0321,R0401,R0921,R0922,R0923,W0101,W0102,W0104,W0105,W0106,W0107,W0108,W0109,W0110,W0120,W0121,W0122,W0141,W0150,W0199,W0211,W0222,W0231,W0233,W0234,W0301,W0311,W0312,W0331,W0332,W0333,W0402,W0403,W0404,W0406,W0410,W0512,W0601,W0602,W0603,W0604,W0612,W0614,W0621,W0622,W0623,W0631,W0632,W0633,W0701,W0702,W0710,W0711,W0712,W1001,W1111,W1201,W1300,W1301,W1401,W1501"

# tolerate these in tests
#  W0201 attribute-defined-outside-init
#  W0223 abstract-method
#  W0232 no-init
#  W0401 wildcard-import
#  W0613 unused-argument
#  W0703 broad-except
#  W1402 anomalous-unicode-escape-in-string
#  R0201 no-self-use
#  E1102 not-callable
ignore_in_tests="W0201,W0223,W0232,W0401,W0613,W0703,W1402,R0201,E1102"


function set_files
{
    files=$(find $path -type f -name '*.py' | tr '\n' ' ')
}

function set_enable
{
    if [ $path == "test" ]; then
        enable_flags=$enable_always
    else
        enable_flags="$enable_always,$ignore_in_tests"
    fi
}


tmp=`mktemp "/tmp/geopy_pylint_out.XXX"`

declare -A paths="geopy test"

for path in $paths; do
    set_files
    set_enable
    pylint \
        --rcfile=./.pylintrc \
        --output-format=text \
        --msg-template='FAIL: {path}:{line} | {msg_id} {symbol}: {obj} {msg}' \
        --disable="all" \
        --enable=$enable_flags \
        $files >> $tmp
done

grep '^FAIL' $tmp
if [ $? -eq 0 ]; then
    exit 1
else
    exit 0
fi
