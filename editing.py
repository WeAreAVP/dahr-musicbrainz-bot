import logging
import urllib
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


class MusicBrainzClient(object):
    def __init__(self, username, password, server="https://test.musicbrainz.org", headless=False):
        self.server = server
        self.username = username
        # self.b = mechanize.Browser()
        # self.b.set_handle_robots(False)
        # self.b.set_debug_redirects(False)
        # self.b.set_debug_http(False)
        # self.b.addheaders = [('User-agent', 'dahr-musicbrainz-bot/1.0 ( %s/user/%s )' % (server, username))]


        ff_options = Options()
        ff_options.headless = headless
        self.b = webdriver.Firefox(options=ff_options)
        self.login(username, password)

    def url(self, path, **kwargs):
        query = ""
        if kwargs:
            query = "?" + urllib.parse.urlencode(
                [(k, v.encode("utf8")) for (k, v) in kwargs.items()]
            )
        return self.server + path + query

    def login(self, username, password):
        login_url = self.url("/login")
        self.b.get(login_url)
        username_field = self.b.find_element(By.ID, "id-username")
        username_field.clear()
        username_field.send_keys(username)

        pw_field = self.b.find_element(By.ID, "id-password")
        pw_field.clear()
        pw_field.send_keys(password)
        pw_field.send_keys(Keys.RETURN)

        WebDriverWait(self.b, 15).until(EC.url_changes(login_url))

        if self.b.current_url != self.url("/user/" + username):
            raise Exception("Unable to login. Is your password correct?")

    # return tuple (normal_edits_left, edits_left)
    def edits_left(self, max_open_edits=2000, max_edits_per_day=1000):

        # Check num of edits made today
        re_found_edits = re.compile(r"Found (?:at least )?([0-9]+(?:,[0-9]+)?) edits?")
        # today = datetime.utcnow().strftime('%Y-%m-%d')
        kwargs = {
            "page": "2000",
            "combinator": "and",
            # 'negation': '0',
            "conditions.0.field": "open_time",
            "conditions.0.operator": ">",
            "conditions.0.args.0": "today",
            "conditions.0.args.1": "",
            "conditions.1.field": "editor",
            "conditions.1.operator": "me",
        }
        url = self.url("/search/edits", **kwargs)
        self.b.get(url)
        page = self.b.page_source
        match = re_found_edits.search(page)
        if not match:
            logging.error("Could not determine remaining daily edits")
            return 0, 0
        edits_today = int(re.sub(r"[^0-9]+", "", match.group(1)))
        edits_left = max_edits_per_day - edits_today
        if edits_left <= 0:
            return 0, 0

        # Check number of open edits
        url = self.url("/user/%s/edits/open" % (self.username,), page="2000")
        self.b.get(url)
        page = self.b.page_source
        match = re_found_edits.search(page)
        if not match:
            logging.error("Could not determine open edits")
            return 0, 0
        open_edits = int(re.sub(r"[^0-9]+", "", match.group(1)))
        normal_edits_left = min(edits_left, max_open_edits - open_edits)
        return normal_edits_left, edits_left

    def add_external_link(self, artist_id, link, edit_note=None):
        # get artist edit page
        artist_url = self.url(f"/artist/{artist_id}")
        artist_edit_url = f"{artist_url}/edit"
        self.b.get(artist_edit_url)

        # wait for JS to load external links table
        WebDriverWait(self.b, 15).until(
            EC.presence_of_element_located((By.ID, "external-links-editor"))
        )

        # check if artist has DAHR link already
        page = self.b.page_source
        re_found_dahr_link = re.compile(r"adp.library.ucsb.edu/names")
        dahr_link_found = re_found_dahr_link.search(page)
        if dahr_link_found:
            logging.info(f"DAHR link already present for MB id {artist_id}")
            return False

        # Add URL
        url_input = self.b.find_element(
            By.XPATH, "//input[@placeholder='Add another link']"
        )
        url_input.clear()
        url_input.send_keys(link)

        # Add edit note
        if edit_note:
            edit_note_field = self.b.find_element(By.ID, "id-edit-artist.edit_note")
            edit_note_field.send_keys(edit_note)

        # Submit edit
        submit_button = self.b.find_element(By.CSS_SELECTOR, "button.submit")
        submit_button.click()

        # wait for edit to go through
        WebDriverWait(self.b, 20).until(EC.url_changes(artist_edit_url))
        if self.b.current_url != artist_url:
            raise Exception("Edit failed")

        return True  # success

    # TODO: check/update this function
    # def cancel_edit(self, edit_nr, edit_note=""):
    #     self.b.open(self.url("/edit/%s/cancel" % (edit_nr,)))
    #     page = self.b.response().read()
    #     self.b.select_form(
    #         predicate=lambda f: f.method == "POST" and "/cancel" in f.action
    #     )
    #     if edit_note:
    #         self.b["confirm.edit_note"] = edit_note.encode("utf8")
    #     self.b.submit()

    def __del__(self):
        # Close selenium when object is removed
        self.b.close()
