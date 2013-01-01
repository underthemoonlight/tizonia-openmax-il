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
 * @file   frprc.c
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 *
 * @brief  Tizonia OpenMAX IL - File Reader processor class implementation
 *
 *
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <assert.h>
#include <stdio.h>

#include "OMX_Core.h"

#include "tizkernel.h"
#include "tizscheduler.h"

#include "frprc.h"
#include "frprc_decls.h"

#include "tizosal.h"

#ifdef TIZ_LOG_CATEGORY_NAME
#undef TIZ_LOG_CATEGORY_NAME
#define TIZ_LOG_CATEGORY_NAME "tiz.file_reader.prc"
#endif

/*
 * frprc
 */

static void *
fr_proc_ctor (void *ap_obj, va_list * app)
{
  struct frprc *p_obj = super_ctor (frprc, ap_obj, app);
  TIZ_LOG (TIZ_LOG_TRACE, "Constructing frprc...[%p]", p_obj);

  p_obj->eos_ = false;

  return p_obj;
}

static void *
fr_proc_dtor (void *ap_obj)
{
  struct frprc *p_obj = ap_obj;
  TIZ_LOG (TIZ_LOG_TRACE, "Destructing frprc...[%p]", p_obj);
  return super_dtor (frprc, ap_obj);
}

static OMX_ERRORTYPE
fr_proc_read_buffer (const void *ap_obj, OMX_BUFFERHEADERTYPE * p_hdr)
{
  struct frprc *p_obj = (struct frprc *) ap_obj;
  (void) p_obj;

  return OMX_ErrorNone;
}

/*
 * from tizservant class
 */

static OMX_ERRORTYPE
fr_proc_allocate_resources (void *ap_obj, OMX_U32 a_pid)
{
  struct frprc *p_obj = ap_obj;
  const struct tizservant *p_parent = ap_obj;

  assert (ap_obj);

  (void) p_parent;
  (void) p_obj;

  TIZ_LOG (TIZ_LOG_TRACE, "Resource allocation complete... "
             "frprc = [%p]!!!", p_obj);

  return OMX_ErrorNone;
}

static OMX_ERRORTYPE
fr_proc_deallocate_resources (void *ap_obj)
{
  struct frprc *p_obj = ap_obj;
  assert (ap_obj);

  (void) p_obj;

  TIZ_LOG (TIZ_LOG_TRACE, "Resource deallocation complete..."
             "frprc = [%p]!!!", p_obj);

  return OMX_ErrorNone;
}

static OMX_ERRORTYPE
fr_proc_prepare_to_transfer (void *ap_obj, OMX_U32 a_pid)
{
  struct frprc *p_obj = ap_obj;
  assert (ap_obj);

  TIZ_LOG (TIZ_LOG_TRACE, "pid [%d]", a_pid);

  TIZ_LOG (TIZ_LOG_TRACE,
             "Prepared to transfer buffers...p_obj = [%p]!!!", p_obj);

  return OMX_ErrorNone;

}

static OMX_ERRORTYPE
fr_proc_transfer_and_process (void *ap_obj, OMX_U32 a_pid)
{
  struct frprc *p_obj = ap_obj;
  assert (ap_obj);

  TIZ_LOG (TIZ_LOG_TRACE, "pid [%d]", a_pid);

  TIZ_LOG (TIZ_LOG_TRACE, "Awaiting buffers...p_obj = [%p]!!!", p_obj);

  return OMX_ErrorNone;
}

static OMX_ERRORTYPE
fr_proc_stop_and_return (void *ap_obj)
{
  struct frprc *p_obj = ap_obj;
  assert (ap_obj);

  TIZ_LOG (TIZ_LOG_TRACE, "Stopped buffer transfer...p_obj = [%p]!!!",
             p_obj);

  return OMX_ErrorNone;
}

/*
 * from tizproc class
 */

static OMX_ERRORTYPE
fr_proc_buffers_ready (const void *ap_obj)
{
  const struct frprc *p_obj = ap_obj;
  const struct tizservant *p_parent = ap_obj;
  tiz_pd_set_t ports;
  void *p_krn = tiz_get_krn (p_parent->ip_hdl);
  OMX_BUFFERHEADERTYPE *p_hdr = NULL;

  TIZ_LOG (TIZ_LOG_TRACE, "Buffers ready...");

  if (!(p_obj->eos_))
    {
      TIZ_PD_ZERO (&ports);

      TIZ_UTIL_TEST_ERR (tizkernel_select (p_krn, 1, &ports));

      if (TIZ_PD_ISSET (0, &ports))
        {
          TIZ_UTIL_TEST_ERR (tizkernel_claim_buffer (p_krn, 0, 0, &p_hdr));
          TIZ_LOG (TIZ_LOG_TRACE, "Claimed HEADER [%p]...", p_hdr);
          TIZ_UTIL_TEST_ERR (fr_proc_read_buffer (ap_obj, p_hdr));
          tizkernel_relinquish_buffer (p_krn, 0, p_hdr);
        }
    }

  return OMX_ErrorNone;
}

/*
 * initialization
 */

const void *frprc;

void
init_frprc (void)
{

  if (!frprc)
    {
      TIZ_LOG (TIZ_LOG_TRACE, "Initializing frprc...");
      init_tizproc ();
      frprc =
        factory_new
        (tizproc_class,
         "frprc",
         tizproc,
         sizeof (struct frprc),
         ctor, fr_proc_ctor,
         dtor, fr_proc_dtor,
         tizproc_buffers_ready, fr_proc_buffers_ready,
         tizservant_allocate_resources, fr_proc_allocate_resources,
         tizservant_deallocate_resources, fr_proc_deallocate_resources,
         tizservant_prepare_to_transfer, fr_proc_prepare_to_transfer,
         tizservant_transfer_and_process, fr_proc_transfer_and_process,
         tizservant_stop_and_return, fr_proc_stop_and_return, 0);
    }

}
