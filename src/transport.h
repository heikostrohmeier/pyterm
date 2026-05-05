#ifndef TRANSPORT_H_
#define TRANSPORT_H_

#include <glib.h>

enum {
	TRANSPORT_SERIAL,
	TRANSPORT_TCP_CLIENT,
	TRANSPORT_TCP_SERVER
};

int     transport_open(void);
void    transport_close(void);
int     transport_send(const char *buf, int len);
int     transport_get_fd(void);
void    transport_send_break(void);
int     transport_get_signals(void);
void    transport_set_signal(int signal);
gchar  *transport_get_status_string(void);

#endif
