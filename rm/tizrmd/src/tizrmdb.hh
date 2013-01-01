/**
 * Copyright (C) 2011-2013 Aratelia Limited - Juan A. Rubio
 *
 * This file is part of Tizonia
 *
 * Tizonia is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * Tizonia is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Tizonia.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * @file   tizrmdb.hh
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 *
 * @brief  Tizonia OpenMAX IL - Resource Manager SQLite3 database handling
 *
 */

#ifndef TIZRMDB_HH
#define TIZRMDB_HH

class sqlite3;

#include <boost/utility.hpp>
#include <string>

#include "tizrmtypes.h"
#include "tizrmowner.hh"

class tizrmdb : boost::noncopyable
{

public:

  explicit tizrmdb(char const * ap_dbname = 0);
  ~tizrmdb();

  tizrm_error_t connect();
  tizrm_error_t disconnect();

  tizrm_error_t acquire_resource(const unsigned int &rid,
                                 const unsigned int &quantity,
                                 const std::string &cname,
                                 const std::vector< unsigned char > &uuid,
                                 const unsigned int &grpid,
                                 const unsigned int &pri);

  tizrm_error_t release_resource(const unsigned int &rid, const unsigned int &quantity,
                                 const std::string &cname,
                                 const std::vector< unsigned char > &uuid,
                                 const unsigned int &grpid,
                                 const unsigned int &pri);

  tizrm_error_t release_all(const std::string &cname,
                            const std::vector< unsigned char > &uuid);

  tizrm_error_t find_owners(const unsigned int &rid,
                            const unsigned int &pri,
                            tizrm_owners_list_t &owners) const;

  bool resource_available(const unsigned int &rid,
                          const unsigned int &quantity) const;

  bool resource_acquired(const std::vector< unsigned char > &uuid,
                         const unsigned int &rid,
                         const unsigned int &quantity) const;

  bool resource_provisioned(const unsigned int &rid) const;

  bool comp_provisioned(const std::string &cname) const;

  bool comp_provisioned_with_resid(const std::string &cname,
                                   const unsigned int &rid) const;

private:

  int open(char const * ap_dbname);
  int close();
  int reset_alloc_table();

  int run_query(char const * ap_sql);
  int run_query(char const * ap_sql) const;

  void print_query_result() const;
  std::string sqlite_error_str(int error) const;

private:

  sqlite3 *pdb_;
  std::string dbname_;
  mutable std::vector<std::string> vcol_head_;
  mutable std::vector<std::string> vdata_;

};

#endif // TIZRMDB_HH
