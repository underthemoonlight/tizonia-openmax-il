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
 * @file   tizvp8port_decls.h
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 * 
 * @brief  vp8port class declarations
 * 
 * 
 */

#ifndef TIZVP8PORT_DECLS_H
#define TIZVP8PORT_DECLS_H

#ifdef __cplusplus
extern "C"
{
#endif

#include "OMX_Component.h"

#include "tizvideoport_decls.h"
#include "tizosal.h"

struct tizvp8port
{
  /* Object */
  const struct tizvideoport _;
  OMX_VIDEO_PARAM_VP8TYPE vp8type_;
  OMX_VIDEO_PARAM_PROFILELEVELTYPE pltype_;
  tiz_vector_t *p_levels_;
  OMX_VIDEO_PARAM_BITRATETYPE pbrtype_;
  OMX_VIDEO_CONFIG_BITRATETYPE cbrtype_;
  OMX_CONFIG_FRAMERATETYPE frtype_;
};

struct tizvp8port_class
{
  /* Class */
  const struct tizvideoport_class _;
};

#ifdef __cplusplus
}
#endif

#endif /* TIZVP8PORT_DECLS_H */
