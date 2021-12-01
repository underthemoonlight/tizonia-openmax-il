/**
 * Copyright (C) 2011-2020 Aratelia Limited - Juan A. Rubio and contributors
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
 * @file   tizgraphops.hpp
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 *
 * @brief  OpenMAX IL graph operations base class
 *
 *
 */

#ifndef TIZGRAPHOPS_HPP
#define TIZGRAPHOPS_HPP

#include <boost/function.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/thread.hpp>

#include <string>

#include <OMX_Core.h>
#include <tizplatform.h>

#include "tizgraphtypes.hpp"
#include "tizplaylist.hpp"
#include "tizprobe.hpp"

#define G_OPS_BAIL_IF_ERROR(exp, str)                                         \
  do                                                                          \
  {                                                                           \
    OMX_ERRORTYPE rc_ = OMX_ErrorNone;                                        \
    if (OMX_ErrorNone != (rc_ = (exp)))                                       \
    {                                                                         \
      record_error (rc_, str);                                                \
      TIZ_LOG (TIZ_PRIORITY_ERROR, "[%s] : %s", tiz_err_to_str (error_code_), \
               error_msg_.c_str ());                                          \
      return;                                                                 \
    }                                                                         \
  } while (0)

// Same as above, but this macro only records the error. It does not leave the
// current function
#define G_OPS_RECORD_IF_ERROR(exp, str)                                       \
  do                                                                          \
  {                                                                           \
    OMX_ERRORTYPE rc_ = OMX_ErrorNone;                                        \
    if (OMX_ErrorNone != (rc_ = (exp)))                                       \
    {                                                                         \
      record_error (rc_, str);                                                \
      TIZ_LOG (TIZ_PRIORITY_ERROR, "[%s] : %s", tiz_err_to_str (error_code_), \
               error_msg_.c_str ());                                          \
    }                                                                         \
  } while (0)

namespace tiz
{
  // Forward declaration
  namespace graphmgr
  {
    class mgr;
  }

  namespace graph
  {
    // Forward declaration
    class cbackhandler;

    class ops
    {
    public:
      static const int INVALID_POSITION = -1;
      static const int SKIP_DEFAULT_VALUE = 1;

    public:
      ops (graph *p_graph, const omx_comp_name_lst_t &comp_lst,
           const omx_comp_role_lst_t &role_lst);
      virtual ~ops ();

      void set_manager (graphmgr::mgr *ap_mgr);

    public:
      virtual void do_load ();
      virtual void do_load_comp (const int comp_id);
      virtual void do_setup ();
      virtual void do_setup_tunnel (const int tunnel_id);
      virtual void do_ack_loaded ();
      virtual void do_store_config (const tizgraphconfig_ptr_t &config);
      virtual void do_enable_auto_detection (const int handle_id,
                                             const int port_id);
      virtual void do_disable_comp_ports (const int comp_id, const int port_id);
      virtual void do_disable_tunnel (const int tunnel_id);
      virtual void do_enable_comp_ports (const int comp_id, const int port_id);
      virtual void do_enable_tunnel (const int tunnel_id);
      virtual void do_flush_tunnel (const int tunnel_id);
      virtual void do_reconfigure_tunnel (const int tunnel_id);
      virtual void do_probe ();
      virtual void do_configure ();
      virtual void do_configure_comp (const int comp_id);
      virtual void do_loaded2idle ();
      virtual void do_loaded2idle_comp (const int comp_id);
      virtual void do_loaded2idle_tunnel (const int tunnel_id);
      virtual void do_idle2exe ();
      virtual void do_idle2exe_comp (const int comp_id);
      virtual void do_idle2exe_tunnel (const int tunnel_id);
      virtual void do_ack_execd ();
      virtual void do_ack_stopped ();
      virtual void do_ack_paused ();
      virtual void do_ack_resumed ();
      virtual void do_ack_metadata ();
      virtual void do_ack_volume ();
      virtual void do_exe2pause ();
      virtual void do_pause2exe ();
      virtual void do_pause2idle ();
      virtual void do_exe2idle ();
      virtual void do_exe2idle_comp (const int comp_id);
      virtual void do_idle2loaded ();
      virtual void do_idle2loaded_comp (const int comp_id);
      virtual void do_seek ();
      virtual void do_skip ();
      virtual void do_print_playlist ();
      virtual void do_add_playlist ();
      virtual void do_store_position (const int pos);
      virtual void do_store_skip (const int jump);
      virtual void do_volume_step (const int step);
      virtual void do_volume (const double vol);
      virtual void do_restore_volume ();
      virtual void do_mute ();
      virtual void do_error ();
      virtual void do_end_of_play ();
      virtual void do_tear_down_tunnels ();
      virtual void do_destroy_graph ();
      virtual void do_destroy_comp (const int handle_id);
      virtual void do_ack_unloaded ();
      virtual void do_record_destination (
          const OMX_STATETYPE destination_state);
      virtual void do_retrieve_metadata ();
      virtual void do_reset_internal_error ();
      virtual void do_record_fatal_error (const OMX_HANDLETYPE handle,
                                          const OMX_ERRORTYPE error,
                                          const OMX_U32 port,
                                          const OMX_PTR p_eventdata = NULL);
      virtual void do_start_progress_display();
      virtual void do_increase_progress_display(void *ap_arg1, const unsigned int a_id);
      virtual void do_pause_progress_display();
      virtual void do_resume_progress_display();
      virtual void do_stop_progress_display();

      virtual bool is_port_settings_evt_required () const;
      virtual bool is_disabled_evt_required () const;
      virtual bool is_fatal_error (const OMX_ERRORTYPE error) const;
      virtual bool is_tunnel_altered (const int tunnel_id,
                                      const OMX_HANDLETYPE handle,
                                      const OMX_U32 port_id,
                                      const OMX_INDEXTYPE index_id) const;
      virtual bool is_skip_allowed () const;

      OMX_ERRORTYPE internal_error () const;
      std::string internal_error_msg () const;

    public:
      bool is_last_component (const OMX_HANDLETYPE handle) const;
      bool is_first_component (const OMX_HANDLETYPE handle) const;
      bool is_trans_complete (const OMX_HANDLETYPE handle,
                              const OMX_STATETYPE to_state);
      bool is_destination_state (const OMX_STATETYPE to_state);
      bool is_component_state (const int handle_id,
                               const OMX_STATETYPE state_id);
      bool is_port_disabling_complete (const OMX_HANDLETYPE handle,
                                       const OMX_U32 port_id);
      bool is_port_enabling_complete (const OMX_HANDLETYPE handle,
                                      const OMX_U32 port_id);
      bool last_op_succeeded () const;
      bool is_end_of_play () const;
      bool is_probing_result_ok () const;

      std::string handle2name (const OMX_HANDLETYPE handle) const;

    protected:
      virtual void record_error (const OMX_ERRORTYPE err_code,
                                 const std::string &err_msg);

      virtual void clear_expected_transitions ();
      virtual void record_expected_transitions (const OMX_STATETYPE to_state);
      virtual void add_expected_transition (const OMX_HANDLETYPE handle,
                                            const OMX_STATETYPE to_state,
                                            const OMX_ERRORTYPE error
                                            = OMX_ErrorNone);

      virtual void clear_expected_port_transitions ();
      virtual void add_expected_port_transition (
          const OMX_HANDLETYPE handle, const OMX_U32 port_id,
          const OMX_COMMANDTYPE disable_or_enable,
          const OMX_ERRORTYPE error = OMX_ErrorNone);

      virtual bool is_port_transition_complete (
          const OMX_HANDLETYPE handle, const OMX_U32 port_id,
          const OMX_COMMANDTYPE disable_or_enable);

      typedef void (tiz::probe::*stream_info_dump_func_t) (void);
      virtual OMX_ERRORTYPE probe_stream (
          const OMX_PORTDOMAINTYPE omx_domain, const int omx_coding,
          const std::string &graph_id, const std::string &graph_action,
          stream_info_dump_func_t stream_info_dump_f, const bool quiet = false);

      virtual bool probe_stream_hook ();
      virtual OMX_ERRORTYPE transition_source (const OMX_STATETYPE to_state);
      virtual OMX_ERRORTYPE transition_comp (const int comp_id,
                                             const OMX_STATETYPE to_state);
      virtual OMX_ERRORTYPE transition_tunnel (const int tunnel_id,
                                               const OMX_STATETYPE to_state,
                                               const OMX_STATETYPE from_state);
      virtual OMX_ERRORTYPE switch_tunnel (
          const int tunnel_id, const OMX_COMMANDTYPE to_disabled_or_enabled);

      virtual OMX_ERRORTYPE dump_metadata_item (const OMX_U32 index,
                                                const int comp_index,
                                                const bool use_first_as_heading
                                                = true);

      virtual void store_last_track_duration(const char * p_value);

      cbackhandler &get_cback_handler () const;

    protected:
      graph *p_graph_;
      tizprobe_ptr_t probe_ptr_;
      omx_comp_name_lst_t comp_lst_;
      omx_comp_role_lst_t role_lst_;
      omx_comp_handle_lst_t handles_;
      omx_hdl2name_map_t h2n_;
      tizgraphconfig_ptr_t config_;
      omx_event_info_lst_t expected_transitions_lst_;
      omx_event_info_lst_t expected_port_transitions_lst_;
      tizplaylist_ptr_t playlist_;
      int position_;
      int jump_;
      OMX_STATETYPE destination_state_;
      track_metadata_map_t metadata_;
      int volume_;
      unsigned long duration_;
      OMX_ERRORTYPE error_code_;
      std::string error_msg_;
    };

  }  // namespace graph
}  // namespace tiz

#endif  // TIZGRAPHOPS_HPP
