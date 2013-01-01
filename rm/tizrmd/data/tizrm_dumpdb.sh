#!/bin/bash
#
# Copyright (C) 2011-2013 Aratelia Limited - Juan A. Rubio
#
# This file is part of Tizonia
#
# Tizonia is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Tizonia is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Tizonia.  If not, see <http://www.gnu.org/licenses/>.

SQLITE3=$(which sqlite3)
BASEDIR=$(dirname $0)

if [ -z "$1" ];
then
    TIZRM_DB_NAME=${BASEDIR}"/tizrm.db"
else
    TIZRM_DB_NAME=$1
fi

if [ -f $TIZRM_DB_NAME ];
then 
    echo -e .dump | $SQLITE3 $TIZRM_DB_NAME > /tmp/$2
    cat /tmp/$2
    echo -e "Dumped $TIZRM_DB_NAME database to /tmp/$2..."
fi

echo -e "Done."

