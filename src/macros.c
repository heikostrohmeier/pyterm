/***********************************************************************/
/* macros.c                                                            */
/* --------                                                            */
/*           GTKTerm Software                                          */
/*                      (c) Julien Schmitt                             */
/*                                                                     */
/* ------------------------------------------------------------------- */
/*                                                                     */
/*   Purpose                                                           */
/*      Functions for the management of the macros                     */
/*                                                                     */
/*   ChangeLog                                                         */
/*      - 0.99.2 : Internationalization                                */
/*      - 0.99.0 : file creation by Julien                             */
/*                                                                     */
/***********************************************************************/

#include <gdk/gdk.h>
#include <gdk/gdkkeysyms.h>
#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "interface.h"
#include "macros.h"
#include "term_config.h"

#include <config.h>
#include <glib/gi18n.h>

enum
{
  COLUMN_SHORTCUT,
  COLUMN_LABEL,
  COLUMN_ACTION,
  COLUMN_TAB,
  NUM_COLUMNS
};

macro_t *macros = NULL;
static GtkWidget *window = NULL;

macro_t *
get_shortcuts (gint *size)
{
  gint i = 0;

  if (macros != NULL)
    {
      while (macros[i].shortcut != NULL || macros[i].label != NULL)
        i++;
    }
  *size = i;
  return macros;
}

/* Parse une séquence hexadécimale après un backslash (\XX ou \0XX) */
static guchar
parse_hex_escape (const gchar *string, gint *index)
{
  gint i = *index;
  gint hex_start = 0;
  gint isTwodigits = 0;

  /* Déterminer où commence la partie hexa et combien de digits on a */
  if (string[i + 1] == '0' && g_unichar_isxdigit ((gunichar) string[i + 2]))
    {
      // Format \0XX ou \0X
      hex_start = i + 2;
      isTwodigits = g_unichar_isxdigit ((gunichar) string[i + 3]) ? 1 : 0;
    }
  else if (g_unichar_isxdigit ((gunichar) string[i + 1]))
    {
      // Format \XX ou \X
      hex_start = i + 1;
      isTwodigits = g_unichar_isxdigit ((gunichar) string[i + 2]) ? 1 : 0;
    }
  else
    { // finalement, mauvais format, on sort les caractaire ascii tel quel
      return '\\';
    }

  /* Parser les digits hexa */
  guint val_read;
  if (sscanf (&string[hex_start], "%02X", &val_read) == 1)
    {
      /* Mettre l'index sur le dernier caractère utiliser */
      *index = hex_start + isTwodigits;
      return (guchar) val_read;
    }

  return '\\';
}
/* Parse une séquence d'échappement C standard (\n, \t, etc.) */
static guchar
parse_standard_escape (gchar escape_char, gint *index)
{
  guchar result;

  switch (escape_char)
    {
    case 'a':
      result = '\a';
      break;
    case 'b':
      result = '\b';
      break;
    case 't':
      result = '\t';
      break;
    case 'n':
      result = '\n';
      break;
    case 'v':
      result = '\v';
      break;
    case 'f':
      result = '\f';
      break;
    case 'r':
      result = '\r';
      break;
    case '\\':
      result = '\\';
      break;
    default:
      return '\\'; // séquence inconue, retourne \ et n'avance pas
    }

  (*index)++;
  return result;
}

/* Parse une chaîne de macro et construit le buffer à envoyer */
static GByteArray *
parse_macro_string (const gchar *string)
{
  guchar byte;
  GByteArray *buffer = g_byte_array_new ();
  gint length = strlen (string);

  for (gint i = 0; i < length; i++)
    {
      if (string[i] == '\\' && string[i + 1] != '\0')
        {
          if (g_unichar_isdigit ((gunichar) string[i + 1]))
            {
              byte = parse_hex_escape (string, &i);
            }
          else
            {
              byte = parse_standard_escape (string[i + 1], &i);
            }
        }
      else
        {
          byte = (guchar) string[i];
        }

      g_byte_array_append (buffer, &byte, 1);
    }

  return buffer;
}

/* Parse le spécificateur de format à action[start] (où action[start]=='%' et action[start+1]!='%').
   Retourne le type char ('d','f','s'...) et écrit la position du type dans *end_out. */
static gchar
parse_one_spec (const gchar *action, gint start, gint *end_out)
{
  gint j = start + 1;
  while (action[j] == '-' || action[j] == '+' || action[j] == ' ' ||
         action[j] == '#' || action[j] == '0')
    j++;
  while (g_ascii_isdigit (action[j]))
    j++;
  if (action[j] == '.')
    {
      j++;
      while (g_ascii_isdigit (action[j]))
        j++;
    }
  while (action[j] == 'h' || action[j] == 'l' || action[j] == 'L' ||
         action[j] == 'z' || action[j] == 'j' || action[j] == 't')
    j++;
  if (action[j] != '\0' && strchr ("diouxXeEfFgGaAcs", action[j]))
    {
      if (end_out)
        *end_out = j;
      return action[j];
    }
  return '\0';
}

/* Applique un spécificateur isolé sur une valeur string et retourne le résultat alloué. */
static gchar *
apply_spec (const gchar *spec, gchar fmt_type, const gchar *arg_str)
{
  switch (fmt_type)
    {
    case 'd':
    case 'i':
      return g_strdup_printf (spec, (int) strtol (arg_str, NULL, 10));
    case 'u':
    case 'o':
      return g_strdup_printf (spec, (unsigned int) strtoul (arg_str, NULL, 10));
    case 'x':
    case 'X':
      return g_strdup_printf (spec, (unsigned int) strtoul (arg_str, NULL, 0));
    case 'e':
    case 'E':
    case 'f':
    case 'F':
    case 'g':
    case 'G':
    case 'a':
    case 'A':
      return g_strdup_printf (spec, strtod (arg_str, NULL));
    case 's':
      return g_strdup_printf (spec, arg_str);
    case 'c':
      return g_strdup_printf (spec, (int) (arg_str[0] ? arg_str[0] : ' '));
    default:
      return g_strdup ("");
    }
}

gchar
macro_get_format_type (const gchar *action)
{
  if (action == NULL)
    return '\0';
  for (gint i = 0; action[i] != '\0'; i++)
    {
      if (action[i] != '%')
        continue;
      if (action[i + 1] == '%')
        {
          i++;
          continue;
        }
      gchar t = parse_one_spec (action, i, NULL);
      if (t != '\0')
        return t;
    }
  return '\0';
}

gboolean
macro_has_format_arg (const gchar *action)
{
  return macro_get_format_type (action) != '\0';
}

gint
macro_count_format_args (const gchar *action)
{
  if (action == NULL)
    return 0;
  gint count = 0;
  for (gint i = 0; action[i] != '\0'; i++)
    {
      if (action[i] != '%')
        continue;
      if (action[i + 1] == '%')
        {
          i++;
          continue;
        }
      gint end;
      if (parse_one_spec (action, i, &end) != '\0')
        {
          count++;
          i = end;
        }
    }
  return count;
}

/* Retourne un tableau de types (ex: "dfs") à libérer avec g_free, ou NULL si aucun arg. */
gchar *
macro_get_format_types (const gchar *action, gint *count_out)
{
  gint n = macro_count_format_args (action);
  if (count_out)
    *count_out = n;
  if (n == 0)
    return NULL;
  gchar *types = g_new (gchar, n + 1);
  gint idx = 0;
  for (gint i = 0; action[i] != '\0' && idx < n; i++)
    {
      if (action[i] != '%')
        continue;
      if (action[i + 1] == '%')
        {
          i++;
          continue;
        }
      gint end;
      gchar t = parse_one_spec (action, i, &end);
      if (t != '\0')
        {
          types[idx++] = t;
          i = end;
        }
    }
  types[n] = '\0';
  return types;
}

/* Construit la chaîne d'action en substituant chaque spécificateur par l'argument correspondant. */
static gchar *
format_action_with_args (const gchar *action, const gchar **args, gint n_args)
{
  GString *result = g_string_new ("");
  gint arg_idx = 0;

  for (gint i = 0; action[i] != '\0'; i++)
    {
      if (action[i] != '%')
        {
          g_string_append_c (result, action[i]);
          continue;
        }
      if (action[i + 1] == '%')
        {
          g_string_append_c (result, '%');
          i++;
          continue;
        }

      gint spec_end;
      gchar fmt_type = parse_one_spec (action, i, &spec_end);

      if (fmt_type == '\0')
        {
          g_string_append_c (result, action[i]);
          continue;
        }

      if (arg_idx < n_args)
        {
          gchar *spec = g_strndup (&action[i], spec_end - i + 1);
          gchar *formatted = apply_spec (spec, fmt_type, args[arg_idx] ? args[arg_idx] : "");
          g_string_append (result, formatted);
          g_free (formatted);
          g_free (spec);
          arg_idx++;
        }
      else
        {
          g_string_append_len (result, &action[i], spec_end - i + 1);
        }
      i = spec_end;
    }
  return g_string_free (result, FALSE);
}

void
send_macro_with_args (gint macro_index, const gchar **args, gint n_args)
{
  gint nb_macros = 0;
  get_shortcuts (&nb_macros);
  if (macro_index >= nb_macros || macros[macro_index].action == NULL)
    return;

  gchar *formatted = format_action_with_args (macros[macro_index].action, args, n_args);
  GByteArray *buffer = parse_macro_string (formatted);
  g_free (formatted);

  if (buffer->len > 0)
    send_serial ((gchar *) buffer->data, buffer->len);
  g_byte_array_free (buffer, TRUE);

  gchar *message = g_strdup_printf (_ ("Macro \"%s\" sent!"),
                                    strlen (macros[macro_index].label) > 0 ? macros[macro_index].label : macros[macro_index].shortcut);
  Put_temp_message (message, 800);
  g_free (message);
}

void
send_macro_with_arg (gint macro_index, const gchar *arg_str)
{
  const gchar *args[] = { arg_str };
  send_macro_with_args (macro_index, args, 1);
}

/* Fonction principale de callback pour l'exécution d'une macro */
void
shortcut_callback (gpointer number)
{
  gint macro_index = GPOINTER_TO_INT (number);
  /* Récupérer la chaîne de la macro */
  gchar *macro_string = macros[macro_index].action;

  /* Parser et construire le buffer */
  GByteArray *buffer = parse_macro_string (macro_string);

  /* Envoyer tout le buffer d'un seul coup */
  if (buffer->len > 0)
    send_serial ((gchar *) buffer->data, buffer->len);

  /* Libérer le buffer */
  g_byte_array_free (buffer, TRUE);

  /* Afficher le message de confirmation */
  gchar *message = g_strdup_printf (_ ("Macro \"%s\" sent!"), strlen (macros[macro_index].label) > 0 ? macros[macro_index].label : macros[macro_index].shortcut);
  Put_temp_message (message, 800);
  g_free (message);
}

void
create_shortcuts (macro_t *macro, gint size)
{
  macros = g_malloc ((size + 1) * sizeof (macro_t));
  if (macros != NULL)
    {
      memcpy (macros, macro, size * sizeof (macro_t));
      macros[size].label = NULL;
      macros[size].shortcut = NULL;
      macros[size].action = NULL;
      macros[size].tab = NULL;
    }
  else
    perror ("malloc");
}

void
add_shortcuts (void)
{
  long i = 0;
  guint acc_key;
  GdkModifierType mod;

  if (macros == NULL)
    return;

  while (macros[i].shortcut != NULL)
    {
      macros[i].closure = g_cclosure_new_swap (G_CALLBACK (shortcut_callback), (gpointer) i, NULL);
      gtk_accelerator_parse (macros[i].shortcut, &acc_key, &mod);
      if (acc_key != 0)
        gtk_accel_group_connect (shortcuts, acc_key, mod, GTK_ACCEL_MASK, macros[i].closure);
      i++;
    }
}

static void
macros_destroy (void)
{
  gint i = 0;

  if (macros == NULL)
    return;

  while (macros[i].shortcut != NULL)
    {
      g_free (macros[i].shortcut);
      g_free (macros[i].action);
      g_free (macros[i].label);
      g_free (macros[i].tab);
      g_strfreev (macros[i].args);
      /*
      g_closure_unref(macros[i].closure);
      */
      i++;
    }
  g_free (macros);
  macros = NULL;
}

void
remove_shortcuts (void)
{
  gint i = 0;

  if (macros == NULL)
    return;

  while (macros[i].shortcut != NULL)
    {
      gtk_accel_group_disconnect (shortcuts, macros[i].closure);
      i++;
    }

  macros_destroy ();
}

static GtkTreeModel *
create_model (void)
{
  gint i = 0;
  GtkListStore *store;
  GtkTreeIter iter;

  /* create list store */
  store = gtk_list_store_new (NUM_COLUMNS,
                              G_TYPE_STRING,
                              G_TYPE_STRING,
                              G_TYPE_STRING,
                              G_TYPE_STRING);

  /* add data to the list store */
  if (macros != NULL)
    {
      while (1)
        {
          if (macros[i].shortcut == NULL && macros[i].action == NULL && macros[i].label == NULL)
            break;

          gtk_list_store_append (store, &iter);
          gtk_list_store_set (store, &iter,
                              COLUMN_LABEL, macros[i].label,
                              COLUMN_SHORTCUT, macros[i].shortcut,
                              COLUMN_ACTION, macros[i].action,
                              COLUMN_TAB, macros[i].tab ? macros[i].tab : "",
                              -1);
          i++;
        }
    }

  return GTK_TREE_MODEL (store);
}

static gboolean
action_edited (GtkCellRendererText *cell,
               const gchar *path_string,
               const gchar *new_text,
               gpointer data)
{
  GtkTreeModel *model = (GtkTreeModel *) data;
  GtkTreePath *path = gtk_tree_path_new_from_string (path_string);
  GtkTreeIter iter;

  gtk_tree_model_get_iter (model, &iter, path);

  gtk_list_store_set (GTK_LIST_STORE (model), &iter, COLUMN_ACTION, new_text, -1);
  gtk_tree_path_free (path);

  return TRUE;
}

static gboolean
label_edited (GtkCellRendererText *cell,
              const gchar *path_string,
              const gchar *new_text,
              gpointer data)
{
  GtkTreeModel *model = (GtkTreeModel *) data;
  GtkTreePath *path = gtk_tree_path_new_from_string (path_string);
  GtkTreeIter iter;

  gtk_tree_model_get_iter (model, &iter, path);

  gtk_list_store_set (GTK_LIST_STORE (model), &iter, COLUMN_LABEL, new_text, -1);
  gtk_tree_path_free (path);

  return TRUE;
}

static gboolean
tab_edited (GtkCellRendererText *cell,
            const gchar *path_string,
            const gchar *new_text,
            gpointer data)
{
  GtkTreeModel *model = (GtkTreeModel *) data;
  GtkTreePath *path = gtk_tree_path_new_from_string (path_string);
  GtkTreeIter iter;

  gtk_tree_model_get_iter (model, &iter, path);

  gtk_list_store_set (GTK_LIST_STORE (model), &iter, COLUMN_TAB, new_text, -1);
  gtk_tree_path_free (path);

  return TRUE;
}

static void
add_columns (GtkTreeView *treeview)
{
  GtkCellRenderer *renderer;
  GtkTreeViewColumn *column;
  GtkTreeModel *model = gtk_tree_view_get_model (treeview);

  renderer = gtk_cell_renderer_text_new ();
  g_signal_connect (renderer, "edited", G_CALLBACK (label_edited), model);
  g_object_set (G_OBJECT (renderer), "editable", TRUE, NULL);
  column = gtk_tree_view_column_new_with_attributes (_ ("Label"), renderer, "text", COLUMN_LABEL, NULL);
  gtk_tree_view_column_set_sort_column_id (column, COLUMN_LABEL);
  gtk_tree_view_append_column (treeview, column);

  renderer = gtk_cell_renderer_text_new ();
  column = gtk_tree_view_column_new_with_attributes (_ ("Shortcut"), renderer, "text", COLUMN_SHORTCUT, NULL);
  gtk_tree_view_column_set_sort_column_id (column, COLUMN_SHORTCUT);
  gtk_tree_view_append_column (treeview, column);

  renderer = gtk_cell_renderer_text_new ();
  g_signal_connect (renderer, "edited", G_CALLBACK (action_edited), model);
  column = gtk_tree_view_column_new_with_attributes (_ ("Action"), renderer, "text", COLUMN_ACTION, NULL);
  g_object_set (G_OBJECT (renderer), "editable", TRUE, NULL);
  gtk_tree_view_column_set_sort_column_id (column, COLUMN_ACTION);
  gtk_tree_view_append_column (treeview, column);

  renderer = gtk_cell_renderer_text_new ();
  g_signal_connect (renderer, "edited", G_CALLBACK (tab_edited), model);
  g_object_set (G_OBJECT (renderer), "editable", TRUE, NULL);
  column = gtk_tree_view_column_new_with_attributes (_ ("Tab"), renderer, "text", COLUMN_TAB, NULL);
  gtk_tree_view_column_set_sort_column_id (column, COLUMN_TAB);
  gtk_tree_view_append_column (treeview, column);
}

static gint
Add_shortcut (GtkWidget *button, gpointer pointer)
{
  GtkTreeIter iter;
  GtkTreeModel *model = (GtkTreeModel *) pointer;

  gtk_list_store_append (GTK_LIST_STORE (model), &iter);

  gtk_list_store_set (GTK_LIST_STORE (model), &iter,
                      COLUMN_SHORTCUT, "None",
                      COLUMN_TAB, _ ("General"),
                      -1);

  return FALSE;
}

static gboolean
Delete_macro (GtkWidget *button, gpointer pointer)
{
  GtkTreeIter iter;
  GtkTreeView *treeview = (GtkTreeView *) pointer;
  GtkTreeModel *model = gtk_tree_view_get_model (treeview);
  GtkTreeSelection *selection = gtk_tree_view_get_selection (treeview);

  if (gtk_tree_selection_get_selected (selection, NULL, &iter))
    {
      GtkTreePath *path = gtk_tree_model_get_path (model, &iter);
      gtk_list_store_remove (GTK_LIST_STORE (model), &iter);
      gtk_tree_path_free (path);
    }

  return FALSE;
}

static gboolean
Delete_shortcut (GtkWidget *button, gpointer pointer)
{
  GtkTreeIter iter;
  GtkTreeView *treeview = (GtkTreeView *) pointer;
  GtkTreeModel *model = gtk_tree_view_get_model (treeview);
  GtkTreeSelection *selection = gtk_tree_view_get_selection (treeview);

  if (gtk_tree_selection_get_selected (selection, NULL, &iter))
    {
      gtk_list_store_set (GTK_LIST_STORE (model), &iter, COLUMN_SHORTCUT, "None", -1);
    }

  return FALSE;
}

static gboolean
Save_shortcuts (GtkWidget *button, gpointer pointer)
{
  GtkTreeIter iter;
  GtkTreeView *treeview = (GtkTreeView *) pointer;
  GtkTreeModel *model = gtk_tree_view_get_model (treeview);
  gint i = 0;

  /* Préserver les args existants par index avant de détruire les macros */
  gint old_count = 0;
  macro_t *old_macros = get_shortcuts (&old_count);
  gchar ***saved_args = g_new0 (gchar **, old_count);
  for (gint k = 0; k < old_count; k++)
    if (old_macros[k].args != NULL)
      saved_args[k] = g_strdupv (old_macros[k].args);

  remove_shortcuts ();

  if (gtk_tree_model_get_iter_first (model, &iter))
    {
      do
        {
          i++;
        }
      while (gtk_tree_model_iter_next (model, &iter));

      gtk_tree_model_get_iter_first (model, &iter);
      macros = g_malloc ((i + 1) * sizeof (macro_t));
      i = 0;
      if (macros != NULL)
        {
          do
            {
              gtk_tree_model_get (model, &iter,
                                  COLUMN_LABEL, &(macros[i].label),
                                  COLUMN_SHORTCUT, &(macros[i].shortcut),
                                  COLUMN_ACTION, &(macros[i].action),
                                  COLUMN_TAB, &(macros[i].tab),
                                  -1);

              /* Restaurer les args si le nombre de spécificateurs est identique */
              if (i < old_count && saved_args[i] != NULL &&
                  g_strv_length (saved_args[i]) == (guint) macro_count_format_args (macros[i].action))
                {
                  macros[i].args = saved_args[i];
                  saved_args[i] = NULL;
                }
              else
                {
                  macros[i].args = NULL;
                }
              i++;
            }
          while (gtk_tree_model_iter_next (model, &iter));

          macros[i].label = NULL;
          macros[i].shortcut = NULL;
          macros[i].action = NULL;
          macros[i].tab = NULL;
          macros[i].args = NULL;
        }
    }

  for (gint k = 0; k < old_count; k++)
    g_strfreev (saved_args[k]);
  g_free (saved_args);

  add_shortcuts ();
  rebuild_macro_buttons ();
  save_config_silent ();
  return FALSE;
}

void
macro_set_arg (gint macro_index, gint arg_index, const gchar *value)
{
  gint nb_macros = 0;
  get_shortcuts (&nb_macros);
  if (macro_index >= nb_macros || macros[macro_index].action == NULL)
    return;

  gint n_args = macro_count_format_args (macros[macro_index].action);
  if (arg_index >= n_args)
    return;

  if (macros[macro_index].args == NULL)
    {
      macros[macro_index].args = g_new0 (gchar *, n_args + 1);
      for (gint k = 0; k < n_args; k++)
        macros[macro_index].args[k] = g_strdup ("");
    }

  g_free (macros[macro_index].args[arg_index]);
  macros[macro_index].args[arg_index] = g_strdup (value ? value : "");
}

static gboolean
key_pressed (GtkWidget *window, GdkEventKey *key, gpointer pointer)
{
  GtkTreeIter iter;
  GtkTreeView *treeview = (GtkTreeView *) pointer;
  GtkTreeModel *model = gtk_tree_view_get_model (treeview);
  GtkTreeSelection *selection = gtk_tree_view_get_selection (treeview);
  gchar *str = NULL;

  switch (key->keyval)
    {
    case GDK_KEY_Shift_L:
    case GDK_KEY_Shift_R:
    case GDK_KEY_Control_L:
    case GDK_KEY_Control_R:
    case GDK_KEY_Caps_Lock:
    case GDK_KEY_Shift_Lock:
    case GDK_KEY_Meta_L:
    case GDK_KEY_Meta_R:
    case GDK_KEY_Alt_L:
    case GDK_KEY_Alt_R:
    case GDK_KEY_Super_L:
    case GDK_KEY_Super_R:
    case GDK_KEY_Hyper_L:
    case GDK_KEY_Hyper_R:
    case GDK_KEY_Mode_switch:
      return FALSE;
    default:
      break;
    }

  if (gtk_tree_selection_get_selected (selection, NULL, &iter))
    {
      GtkTreePath *path = gtk_tree_model_get_path (model, &iter);
      str = gtk_accelerator_name (key->keyval, key->state & ~GDK_MOD2_MASK);
      gtk_list_store_set (GTK_LIST_STORE (model), &iter, COLUMN_SHORTCUT, str, -1);

      gtk_tree_path_free (path);
      g_free (str);

      g_signal_handlers_disconnect_by_func (window, G_CALLBACK (key_pressed), pointer);
    }
  return FALSE;
}

static gboolean
Capture_shortcut (GtkWidget *button, gpointer pointer)
{
  g_signal_connect_after (window, "key_press_event", G_CALLBACK (key_pressed), pointer);

  return FALSE;
}

static gboolean
on_window_close (GtkWidget *widget, GdkEvent *event, gpointer pointer)
{
  Save_shortcuts (NULL, pointer);
  return FALSE;
}

static gboolean
Help_screen (GtkWidget *button, gpointer pointer)
{
  GtkWidget *Dialog;

  Dialog = gtk_message_dialog_new (pointer,
                                   GTK_DIALOG_DESTROY_WITH_PARENT,
                                   GTK_MESSAGE_INFO,
                                   GTK_BUTTONS_CLOSE,
                                   _ ("The \"action\" field of a macro is the data to be sent on the port. Text can be entered, but also special chars, like \\n, \\t, \\r, etc. You can also enter hexadecimal data preceded by a '\\'. The hexadecimal data should not begin with a letter (eg. use \\0FF and not \\FF)\nExamples:\n\t\"Hello\\n\" sends \"Hello\" followed by a Line Feed\n\t\"Hello\\0A\" does the same thing but the LF is entered in hexadecimal"));

  gtk_dialog_run (GTK_DIALOG (Dialog));
  gtk_widget_destroy (Dialog);

  return FALSE;
}

void
Config_macros (GtkAction *action, gpointer data)
{
  GtkWidget *vbox, *hbox;
  GtkWidget *sw;
  GtkTreeModel *model;
  GtkWidget *treeview;
  GtkWidget *button;
  GtkWidget *separator;
  g_print ("Config_macros called\n");
  /* create window, etc */
  window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title (GTK_WINDOW (window), _ ("Configure Macros"));

  g_signal_connect (window, "destroy",
                    G_CALLBACK (gtk_widget_destroyed), &window);
  gtk_container_set_border_width (GTK_CONTAINER (window), 8);

  vbox = gtk_box_new (GTK_ORIENTATION_VERTICAL, 8);
  gtk_container_add (GTK_CONTAINER (window), vbox);

  sw = gtk_scrolled_window_new (NULL, NULL);
  gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (sw),
                                       GTK_SHADOW_ETCHED_IN);
  gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (sw),
                                  GTK_POLICY_NEVER,
                                  GTK_POLICY_AUTOMATIC);
  gtk_box_pack_start (GTK_BOX (vbox), sw, TRUE, TRUE, 0);

  /* create tree model */
  model = create_model ();

  /* create tree view */
  treeview = gtk_tree_view_new_with_model (model);
  gtk_tree_view_set_rules_hint (GTK_TREE_VIEW (treeview), TRUE);
  gtk_tree_view_set_search_column (GTK_TREE_VIEW (treeview),
                                   COLUMN_SHORTCUT);

  g_object_unref (model);

  gtk_container_add (GTK_CONTAINER (sw), treeview);

  /* add columns to the tree view */
  add_columns (GTK_TREE_VIEW (treeview));

  g_signal_connect (window, "delete-event", G_CALLBACK (on_window_close), (gpointer) treeview);

  hbox = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 4);
  gtk_box_set_homogeneous (GTK_BOX (hbox), TRUE);
  gtk_box_pack_start (GTK_BOX (vbox), hbox, FALSE, FALSE, 0);

  button = gtk_button_new_with_mnemonic (_ ("_Add"));
  g_signal_connect (button, "clicked", G_CALLBACK (Add_shortcut), (gpointer) model);
  gtk_box_pack_start (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  button = gtk_button_new_with_mnemonic (_ ("_Delete"));
  g_signal_connect (button, "clicked", G_CALLBACK (Delete_macro), (gpointer) treeview);
  gtk_box_pack_start (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  button = gtk_button_new_with_mnemonic (_ ("_Capture Shortcut"));
  g_signal_connect (button, "clicked", G_CALLBACK (Capture_shortcut), (gpointer) treeview);
  gtk_box_pack_start (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  button = gtk_button_new_with_mnemonic ("Delete Shortcut");
  g_signal_connect (button, "clicked", G_CALLBACK (Delete_shortcut), (gpointer) treeview);
  gtk_box_pack_start (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  separator = gtk_separator_new (GTK_ORIENTATION_HORIZONTAL);
  gtk_box_pack_start (GTK_BOX (vbox), separator, FALSE, TRUE, 0);

  hbox = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 4);
  gtk_box_set_homogeneous (GTK_BOX (hbox), TRUE);
  gtk_box_pack_start (GTK_BOX (vbox), hbox, FALSE, FALSE, 0);

  button = gtk_button_new_from_stock (GTK_STOCK_HELP);
  g_signal_connect (button, "clicked", G_CALLBACK (Help_screen), (gpointer) window);
  gtk_box_pack_start (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  button = gtk_button_new_from_stock (GTK_STOCK_OK);
  g_signal_connect (button, "clicked", G_CALLBACK (Save_shortcuts), (gpointer) treeview);
  g_signal_connect_swapped (button, "clicked", G_CALLBACK (gtk_widget_destroy), (gpointer) window);
  gtk_box_pack_end (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  button = gtk_button_new_from_stock (GTK_STOCK_CANCEL);
  g_signal_connect_swapped (button, "clicked", G_CALLBACK (gtk_widget_destroy), (gpointer) window);
  gtk_box_pack_end (GTK_BOX (hbox), button, TRUE, TRUE, 0);

  gtk_window_set_default_size (GTK_WINDOW (window), 300, 400);

  gtk_widget_show_all (window);
}

