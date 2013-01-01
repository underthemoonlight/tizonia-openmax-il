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
 * @file   tizosalsync.h
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 *
 * @brief Tizonia OpenMAX IL - Semaphore, mutex, and condition variable
 *
 *
 */

#ifndef TIZOSALSYNC_H
#define TIZOSALSYNC_H

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @defgroup sync Semaphore, mutex, and condition variable
 * @ingroup Tizonia-OSAL
 */

#include <OMX_Core.h>
#include <OMX_Types.h>

#define TIZ_STATIC_MUTEX NULL
#define TIZ_STATIC_CONDITION  NULL

  /**
   * Mutex hdl
   * @ingroup sync
   */
  typedef void *tiz_mutex_t;

  /**
   * Semaphore hdl
   * @ingroup sync
   */
  typedef void *tiz_sem_t;

  /**
   * Handle to a conditional variable
   * @ingroup sync
   */
  typedef void *tiz_cond_t;

  /* Semaphore handling */

  /**
   * Initialize a semaphore object using the given value.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorInsufficientResources or
   * OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_sem_init (tiz_sem_t * ap_sem, OMX_U32 a_value);

  /**
   * Free the resources associated with a semaphore object.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_sem_destroy (tiz_sem_t * ap_sem);

  /**
   * Wait for a semaphore being posted.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_sem_wait (tiz_sem_t * ap_sem);

  /**
   * Post semaphore.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_sem_post (tiz_sem_t * ap_sem);

  /**
   * Get the current value of a semaphore object stored it in *ap_sval.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_sem_getvalue (tiz_sem_t * ap_sem, OMX_S32 * ap_sval);

  /* Mutex handling APIs */

  /**
   * Initialize a mutex.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorInsufficientResources or
   * OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_mutex_init (tiz_mutex_t * ap_mutex);

  /**
   * Destroy a mutex.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_mutex_destroy (tiz_mutex_t * ap_mutex);

  /**
   * Lock a mutex.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_mutex_lock (tiz_mutex_t * ap_mutex);

  /**
   * Unlock a mutex.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_mutex_unlock (tiz_mutex_t * ap_mutex);

  /* Conditional variables handling */

  /**
   * Initialize a condition variable.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorInsufficientResources or
   * OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_init (tiz_cond_t * ap_cond);

  /**
   * Destroy a condition variable.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_destroy (tiz_cond_t * ap_cond);

  /**
   * Wake up one thread waiting for a condition variable.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_signal (tiz_cond_t * ap_cond);

  /**
   * Wait for a condition variable to be signaled or broadcast. ap_mutex is
   * assumed to be locked before.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_wait (tiz_cond_t * ap_cond,
                                 tiz_mutex_t * ap_mutex);

  /**
   * Wait for a condition variable to be signaled or broadcast until a_millis
   * milliseconds. ap_mutex is assumed to be locked before.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_timedwait (tiz_cond_t * ap_cond,
                                      tiz_mutex_t * ap_mutex,
                                      OMX_U32 a_millis);

  /**
   * Wake up all threads waiting for a condition variable.
   *
   * @ingroup sync
   *
   * @return OMX_ErrorNone if success, OMX_ErrorUndefined otherwise.
   */
  OMX_ERRORTYPE tiz_cond_broadcast (tiz_cond_t * ap_cond);

#ifdef __cplusplus
}
#endif

#endif                          /* TIZOSALSYNC_H */
