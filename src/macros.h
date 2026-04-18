/***********************************************************************/
/* macros.h                                                            */
/* --------                                                            */
/*           GTKTerm Software                                          */
/*                      (c) Julien Schmitt                             */
/*                                                                     */
/* ------------------------------------------------------------------- */
/*                                                                     */
/*   Purpose                                                           */
/*      Functions for the management of the macros                     */
/*      - Header file -                                                */
/*                                                                     */
/***********************************************************************/

#ifndef MACROS_H_
#define MACROS_H_

typedef struct
{
  gchar *label;
  gchar *shortcut;
  gchar *action;
  gchar *tab;
  gchar **args;    /* valeurs des arguments (%d, %f, %s…), tableau NULL-terminé */
  GClosure *closure;
} macro_t;

void Config_macros (GtkAction *action, gpointer data);
void remove_shortcuts (void);
void add_shortcuts (void);
void create_shortcuts (macro_t *, gint);
void shortcut_callback(gpointer number);
macro_t *get_shortcuts (gint *);
gchar    macro_get_format_type  (const gchar *action);
gboolean macro_has_format_arg   (const gchar *action);
gint     macro_count_format_args(const gchar *action);
gchar   *macro_get_format_types (const gchar *action, gint *count_out);
void     send_macro_with_arg    (gint macro_index, const gchar *arg_str);
void     send_macro_with_args   (gint macro_index, const gchar **args, gint n_args);
void     macro_set_arg          (gint macro_index, gint arg_index, const gchar *value);

#endif

