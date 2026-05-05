/***********************************************************************/
/* serial.c                                                             */
/* -------                                                              */
/*           GTKTerm Software                                           */
/*                      (c) Julien Schmitt                              */
/*                                                                      */
/*   Purpose                                                            */
/*      Serial port / transport access functions                        */
/*      Delegates to transport.c for actual I/O                         */
/*                                                                      */
/***********************************************************************/

#include <gtk/gtk.h>
#include <glib.h>

#include "term_config.h"
#include "serial.h"
#include "transport.h"

#include <config.h>
#include <glib/gi18n.h>

extern struct configuration_port config;

int serial_port_fd = -1;

int Send_chars(char *string, int length)
{
	return transport_send(string, length);
}

gboolean Config_port(void)
{
	return transport_open();
}

void Close_port(void)
{
	transport_close();
	serial_port_fd = transport_get_fd();
}

void Set_signals(guint param)
{
	transport_set_signal((int)param);
}

int lis_sig(void)
{
	return transport_get_signals();
}

void sendbreak(void)
{
	transport_send_break();
}

void configure_echo(gboolean echo)
{
	config.echo = echo;
}

void configure_crlfauto(gboolean crlfauto)
{
	config.crlfauto = crlfauto;
}

void configure_autoreconnect_enable(gboolean autoreconnect)
{
	config.autoreconnect_enabled = autoreconnect;
}

void configure_esc_clear_screen(gboolean esc_clear_screen)
{
	config.esc_clear_screen = esc_clear_screen;
}

gchar *get_port_string(void)
{
	return transport_get_status_string();
}
