#!/bin/python

import curses
import optparse
import select
import sys
import errno
import beanstalkc


class BeanstalkTopUI(object):

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


    def _get_connection(self):
        return beanstalkc.Connection(host=self.options.host, port=int(self.options.port))
        if not self._connection:
            try:
                self._connection = beanstalkc.Connection(host=self.options.host, port=int(self.options.port))
            except beanstalkc.SocketError:
                self.win.erase()
                raise SystemExit('Host {} not contactable on port {}'.format(
                    self.options.host,
                    self.options.port
                    ))
        return self._connection

    connection = property(_get_connection)


    def _format_uptime(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '{}h {}m {}s'.format(hours, minutes, seconds)


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

        titles = (
            'TUBE',
            'READY',
            'URGENT',
            'RESRVD',
            'DELAYD',
            'BURIED',
            )

        overview, lines = self.get_data()

        try:
            overview['uptime'] = self._format_uptime(overview.get('uptime', 0))
        except:
            overview['uptime'] = self._format_uptime(0)

        summary_items = [item.format(**overview) for item in (
            'PID: {pid}',
            'Uptime: {uptime}',
            'Total Jobs: {total-jobs}',
            'Connections: {current-connections} ({current-producers}:{current-workers})',
            'Cur. Tubes: {current-tubes}',
            'Cur. Ready: {current-jobs-ready}',
            'Cur. Urgent: {current-jobs-urgent}',
            'Cur. Buried: {current-jobs-buried}',
            'Cur. Resv\'d: {current-jobs-reserved}',
            )]

        summary_lines = [
            summary_items[0:3],
            summary_items[3:6],
            summary_items[6:],
            ]

        summarywidth = self.width / max(len(i) for i in summary_lines)

        for item in summary_lines:
            line = ''.join(s.ljust(summarywidth) for s in item)
            self.win.addstr(line.ljust(self.width))

        self.win.addstr(' ' * self.width)

        colwidth = self.width / len(titles) + 1

        titlelen = 0
        for i in range(len(titles)):
            attr = curses.A_REVERSE

            if i is 0:
                title = (' ' + titles[i]).ljust(colwidth - 1)
            else:
                title = (titles[i] + ' ').rjust(colwidth - 1)

            titlelen += len(title)
            self.win.addstr(title, attr)

        self.win.addstr(' ' * (self.width - titlelen), curses.A_REVERSE)

        columns = (
            'name',
            'current-jobs-ready',
            'current-jobs-urgent',
            'current-jobs-reserved',
            'current-jobs-delayed',
            'current-jobs-buried',
            )

        max_lines = self.height - (len(summary_lines) + 1)

        sortedlines = sorted(lines, key=lambda x: x['current-jobs-ready'])[::-1]

        for i in range(max_lines):
            try:
                line = sortedlines[i]
            except IndexError:
                break
            row = ''
            for c, column in enumerate(columns):
                try:
                    if c is 0:
                        row += (' ' + str(line[column])).ljust(colwidth - 1)
                    else:
                        row += (str(line[column]) + ' ').rjust(colwidth - 1)

                except curses.error:
                    pass
            try:
                self.win.addstr(row.ljust(self.width))
            except curses.error:
                pass


        self.win.refresh()


    def get_data(self):
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
            return self.connection.stats(), [self.connection.stats_tube(tube) for tube in self.connection.tubes()]
        except (TypeError, beanstalkc.SocketError, beanstalkc.CommandFailed):
            return self.default_overview, [self.default_row]



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

    main_loop = lambda: run_beanstalktop(options)
    main_loop()


if __name__ == '__main__':
    main()
