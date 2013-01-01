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
    COMMANDS=${BASEDIR}"/initrmdb.sql3"
    TIZRM_DB_NAME=${BASEDIR}"/tizrm.db"
else
    COMMANDS=$1
    TIZRM_DB_NAME=$2
fi

if [ -f $TIZRM_DB_NAME ];
then 
    rm $TIZRM_DB_NAME
    echo -e "Deleted old $TIZRM_DB_NAME database..."
fi

echo -e "Populating $TIZRM_DB_NAME using $COMMANDS..."
$SQLITE3 $TIZRM_DB_NAME < $COMMANDS
echo -e "Done."

