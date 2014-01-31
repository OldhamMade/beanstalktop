#!/bin/python

import curses
import optparse
import select
import sys
import errno
import beanstalkc

from operator import itemgetter

class BeanstalkTopUI(object):

    # sort order
    ASCENDING = 1
    DESCENDING = -1

    titles = (
        'TUBE',
        'READY',
        'URGENT',
        'RESRVD',
        'DELAYD',
        'BURIED',
        )

    columns = (
        'name',
        'current-jobs-ready',
        'current-jobs-urgent',
        'current-jobs-reserved',
        'current-jobs-delayed',
        'current-jobs-buried',
        )


    def __init__(self, win, options):
        self.win = win
        self.options = options
        self.resize()
        try:
            curses.use_default_colors()
            curses.start_color()
            curses.curs_set(0)
        except curses.error:
            pass

        self._connection = None

        self.default_overview = dict(
            (i, '-') for i in (
                'pid',
                'total-jobs',
                'current-connections',
                'current-producers',
                'current-workers',
                'current-tubes',
                'current-jobs-ready',
                'current-jobs-urgent',
                'current-jobs-buried',
                'current-jobs-reserved'
                ))

        self.default_row = dict(
            (i, '-') for i in (
                'current-jobs-buried',
                'current-jobs-delayed',
                'current-jobs-ready',
                'current-jobs-reserved',
                'current-jobs-urgent'
                ))

        self.default_row.update({'name': 'default'})

        if curses.has_colors():
            curses.init_pair(1, 255, -1)  # WHITE
            curses.init_pair(2, 245, -1)  # GREY
            curses.init_pair(3, 160, -1)  # RED


    def _get_connection(self):
        return beanstalkc.Connection(host=self.options.host,
                                     port=int(self.options.port))

    connection = property(_get_connection)


    def _format_uptime(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '{0}h {1}m {2}s'.format(hours, minutes, seconds)


    def run(self):
        poll = select.poll()
        poll.register(sys.stdin.fileno(), select.POLLIN | select.POLLPRI)

        while 1:
            self.resize()
            self.refresh_display()

            try:
                events = poll.poll(self.options.delay_seconds * 1000.0)
            except select.error as e:
                if e.args and e.args[0] == errno.EINTR:
                    events = 0
                else:
                    raise
            except KeyboardInterrupt:
                break

            if events:
                key = self.win.getch()
                self.handle_key(key)


    def handle_key(self, key):
        key_bindings = {
            ord('q'): lambda: sys.exit(0),
            ord('Q'): lambda: sys.exit(0),
            }

        action = key_bindings.get(key, lambda: None)
        action()


    def resize(self):
        self.height, self.width = self.win.getmaxyx()


    def refresh_display(self):
        self.win.erase()

        colwidth = self.width / len(self.titles) + 1

        summary_line_height = self.display_header(colwidth)
        title_line_height = self.display_titles(colwidth)
        footer_line_height = self.display_footer(colwidth)

        lines = self.get_tube_data(key='name', sort=self.ASCENDING)

        max_display_lines = self.height - (summary_line_height +
                                           title_line_height +
                                           footer_line_height)

        for i in range(max_display_lines):
            try:
                self.display_line(lines[i], colwidth)
            except IndexError:
                break

        self.win.refresh()


    def display_header(self, colwidth):
        overview = self.get_overview_data()

        try:
            overview['uptime'] = self._format_uptime(overview.get('uptime', 0))
        except:
            overview['uptime'] = self._format_uptime(0)

        summary_items = [item.format(**overview) for item in (
            # Row 1
            'Cur. Resvd: {current-jobs-reserved}',
            'Cur. Urgent: {current-jobs-urgent}',
            ('Cnx\'s: {current-connections} '
             '({current-producers}:{current-workers})'),
            # Row 2
            'Cur. Ready: {current-jobs-ready}',
            'Cur. Buried: {current-jobs-buried}',
            'Up: {uptime}',
            # Row 3
            'Cur. Tubes: {current-tubes}',
            'Total Jobs: {total-jobs}',
            'PID: {pid}',
            )]

        summary_lines = [
            summary_items[0:3],  # Row 1
            summary_items[3:6],  # Row 2
            summary_items[6:],   # Row 3
            ]

        summarywidth = self.width / max(len(i) for i in summary_lines)

        for item in summary_lines:
            line = ''.join(s.ljust(summarywidth) for s in item)
            self.win.addstr(line.ljust(self.width))

        self.win.addstr(' ' * self.width)

        return len(summary_lines)


    def display_titles(self, colwidth):
        titlebar = ''.join([(' ' + self.titles[0]).ljust(colwidth - 1)] +
                           [(title + ' ').rjust(colwidth - 1)
                            for title in self.titles[1:]])

        self.win.addstr(titlebar.ljust(self.width - 1),
                        curses.A_REVERSE|curses.A_STANDOUT)

        return 1


    def display_footer(self, colwidth):
        bottomwin = self.win.subwin(self.height - 1, 0)
        helpmsg = ' To quit, press "q".' # For help, press "h"'
        bottomwin.addstr(helpmsg.ljust(self.width - 1), curses.A_REVERSE)
        return 1


    def display_line(self, line, colwidth):
        row = ''.join([' ' + (str(line[self.columns[0]])).ljust(colwidth - 2)] +
                      [(str(line[column]) + ' ').rjust(colwidth - 1)
                       for column in self.columns[1:]])

        has_jobs = sum([int(line[column])
                        for column in self.columns[1:]
                        if isinstance(line[column], int)
                        or line[column].isdigit()])

        has_burried = int(line.get('current-jobs-burried', 0))

        try:
            if curses.has_colors():
                if has_burried:
                    attrs = curses.color_pair(3)
                elif has_jobs:
                    attrs = curses.color_pair(1)
                else:
                    attrs = curses.color_pair(2) | curses.A_DIM
            else:
                attrs = None

            self.win.addstr(' ' + row.ljust(self.width), attrs)
        except curses.error:
            pass



    def get_overview_data(self):
        """
        Main statistics
        {
        'binlog-current-index': 0,
        'binlog-max-size': 10485760,
        'binlog-oldest-index': 0,
        'binlog-records-migrated': 0,
        'binlog-records-written': 0,
        'cmd-bury': 580,
        'cmd-delete': 15291,
        'cmd-ignore': 3,
        'cmd-kick': 0,
        'cmd-list-tube-used': 0,
        'cmd-list-tubes': 1,
        'cmd-list-tubes-watched': 0,
        'cmd-pause-tube': 0,
        'cmd-peek': 0,
        'cmd-peek-buried': 0,
        'cmd-peek-delayed': 0,
        'cmd-peek-ready': 0,
        'cmd-put': 19623,
        'cmd-release': 0,
        'cmd-reserve': 0,
        'cmd-reserve-with-timeout': 15873,
        'cmd-stats': 1,
        'cmd-stats-job': 22719,
        'cmd-stats-tube': 0,
        'cmd-touch': 0,
        'cmd-use': 10603,
        'cmd-watch': 5,
        'current-connections': 8,
        'current-jobs-buried': 580,
        'current-jobs-delayed': 0,
        'current-jobs-ready': 3750,
        'current-jobs-reserved': 2,
        'current-jobs-urgent': 0,
        'current-producers': 3,
        'current-tubes': 8,
        'current-waiting': 0,
        'current-workers': 3,
        'job-timeouts': 0,
        'max-job-size': 65535,
        'pid': 78938,
        'rusage-stime': 2.585616,
        'rusage-utime': 1.005601,
        'total-connections': 8,
        'total-jobs': 19623,
        'uptime': 156,
        'version': 1.6,
        }
        """
        try:
            return self.connection.stats()
        except (TypeError, beanstalkc.SocketError, beanstalkc.CommandFailed):
            return self.default_overview

    _tube_sort_keys = (
        'cmd-delete',
        'cmd-pause-tube',
        'current-jobs-buried',
        'current-jobs-delayed',
        'current-jobs-ready',
        'current-jobs-reserved',
        'current-jobs-urgent',
        'current-using',
        'current-waiting',
        'current-watching',
        'name',
        'pause',
        'pause-time-left',
        'total-jobs',
        )


    def get_tube_data(self, key='name', sort=1):
        """
        Tube-specific statistics
        {
        'cmd-delete': 892,
        'cmd-pause-tube': 0,
        'current-jobs-buried': 685,
        'current-jobs-delayed': 0,
        'current-jobs-ready': 1001,
        'current-jobs-reserved': 1,
        'current-jobs-urgent': 0
        'current-using': 0,
        'current-waiting': 0,
        'current-watching': 1,
        'name': 'default',
        'pause': 0,
        'pause-time-left': 0,
        'total-jobs': 2579,
        }
        """
        try:
            if key not in self._tube_sort_keys:
                key = 'name'

            lines = [self.connection.stats_tube(tube)
                     for tube
                     in self.connection.tubes()]

            if sort == self.DESCENDING:
                return reversed(sorted(lines, key=itemgetter(key)))

            return sorted(lines, key=itemgetter(key))

        except (TypeError, beanstalkc.SocketError, beanstalkc.CommandFailed):
            return [self.default_row]



def run_beanstalktop_window(win, options):
    ui = BeanstalkTopUI(win, options)
    ui.run()


def run_beanstalktop(options):
    return curses.wrapper(run_beanstalktop_window, options)


def main():
    parser = optparse.OptionParser()
    parser.add_option('--host',
                      dest="host",
                      default="0.0.0.0",
                      help="beanstalkd host [0.0.0.0]"
                      )
    parser.add_option('-p', '--port',
                      dest="port",
                      default=11300,
                      help="beanstalkd port [11300]"
                      )
    parser.add_option('-d', '--delay',
                      dest="delay_seconds",
                      default=1,
                      metavar='NUM',
                      help="delay between refreshes [1s]"
                      )

    options, args = parser.parse_args()
    if args:
        parser.error('Unexpected arguments: ' + ' '.join(args))

    main_loop = run_beanstalktop(options)
    curses.wrapper(main_loop)


if __name__ == '__main__':
    main()
