import sublime
import sublime_plugin

# Sublime Text 3 Python 3 compatibility
try:
    import httplib
except ImportError e
    import http.client as httplib

import urllib
import json
import re
import functools

import threading

def strip_tags(value):
    """Returns the given HTML with all tags stripped."""
    return re.sub(r'<[^>]*?>', '', value.encode("ascii", "ignore"))

class SearchDBLPThread(threading.Thread):

    def __init__(self, v, q):
        threading.Thread.__init__(self)
        self.query = q
        self.view = v

    def stop(self):
        if self.isAlive():
            self._Thread__stop()

    def run(self):
        conn = httplib.HTTPConnection("dblp.org")
        params = urllib.urlencode({
            "accc": ":",
            "bnm" :"A",
            "deb" :"0",
            "dm" :"3",
            "eph" : "1",
            "er" : "20",
            "fh" : "1",
            "fhs" :"1",
            "hppwt" : "20",
            "hppoc" : "100",
            "hrd" :"1a",
            "hrw" :"1d",
            "language" : "en",
            "ll" :"2",
            "log" : "/var/log/dblp/error_log",
            "mcc" :"0",
            "mcl" :"80",
            "mcs" :"1000",
            "mcsr" : "40",
            "mo" : "100",
            "name" :"dblpmirror",
            "navigation_mode" : "user",
            "page" :"index.php",
            "path" : "/search/",
            "qi" : "3",
            "qid" :"3",
            "qt" :"H",
            "query" : self.query,
            "rid" :"6",
            "syn" : "0"
            })

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        conn.request("POST", "/autocomplete-php/autocomplete/ajax.php", params, headers)
        response = conn.getresponse()
        if response.status == 200:
            data = response.read()
            parsed_data = (data.split("\n")[30].split("=", 1)[1])
            # mangle ill formed json
            parsed_data = parsed_data.replace("'", "\"")[:-1]
            parsed_data = json.loads(parsed_data)

            regexp = r"<tr><td.*?><a href=\"http://www.dblp.org/rec/bibtex/(.*?)\">.*?</td><td.*?>(.*?)</td><td.*?>(.*?)</td></tr>"

            body = parsed_data["body"]

            result = []
            # Filter the relevant information:
            for match in re.finditer(regexp, body):
                cite_key = "DBLP:" + match.group(1).encode("ascii", "ignore")
                title = strip_tags(match.group(3))

                authors, title = title.split(":", 1)
                result.append([title, authors, cite_key])

            #print result
            sublime.set_timeout(functools.partial(do_response,
                result),1)
            return

        print(response.reason())
        return

def do_response(data):
    """
    Presents the response of the DBLP Query to the user
    """
    def on_done(i):

        if i == -1:
            return

        cite_key = data[i][2]
        view = sublime.active_window().active_view()
        # Get the first selection
        sel = view.sel()[0]
        edit = view.begin_edit()
        view.insert(edit, sel.begin(), "\cite{%s}" % cite_key)
        view.end_edit(edit)

    sublime.active_window().show_quick_panel(data, on_done)


class DblpSearchCommand(sublime_plugin.TextCommand):
    
    _queryThread = None

    def run(self, edit):

        def on_done(q):
            if len(q) > 3:
                if self._queryThread != None:
                    print("Starting Thread...")
                    self._queryThread.stop()
                self._queryThread = SearchDBLPThread(self.view, q)
                self._queryThread.start()


        self.view.window().show_input_panel("DBLP Search:", "", on_done, None, None)
        



