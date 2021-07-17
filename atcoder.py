#!python3.8
# -*- coding: utf-8 -*-

from urllib.parse import urljoin
from datetime import datetime, timezone, timedelta
import re
from typing import Generator, List, Tuple
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import lxml.html


class Session(requests.Session):
    def __init__(self):
        super().__init__()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        self.mount("https://", HTTPAdapter(max_retries=retries))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    def request(self, *args, **kwargs):
        response = super().request(*args, **kwargs)
        response.raise_for_status()
        try:
            response.html = lxml.html.fromstring(response.content)
        except:
            response.html = None
        return response


class AtCoder:
    def __init__(self, username: str, password: str):
        self.session = Session()
        self.login(username, password)

    def login(self, username: str, password: str):
        login_url = 'https://atcoder.jp/login'
        login_page = self.session.get(login_url).html
        form = login_page.xpath('//*[@id="main-container"]/div[1]/div/form')[0]
        form_values = dict(form.form_values())
        form_values['username'] = username
        form_values['password'] = password
        response = self.session.post(login_url, params=form_values)
        if response.url != 'https://atcoder.jp/home':
            raise Exception('username or password is wrong')

    def get_contest(self, contest_name: str):
        return AtCoderContest(self, contest_name)


class AtCoderContest:
    def __init__(self, atcoder: AtCoder, name: str):
        self.atcoder = atcoder
        self.session = self.atcoder.session
        self.name = name
        self.url = f'https://atcoder.jp/contests/{name}'
        self.start_time, self.end_time = self.get_time()

    def get_time(self) -> Tuple[datetime, datetime]:
        contest_page = self.session.get(self.url).html
        script = contest_page.xpath(
            '//script[contains(.//text(), "startTime")]')[0]
        start_time_str = re.search(
            r'\s*var startTime = moment\("(.+)"\);', script.text_content())[1]
        end_time_str = re.search(
            r'\s*var endTime = moment\("(.+)"\);', script.text_content())[1]
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        return start_time, end_time

    def get_sec_to_start(self) -> float:
        now = datetime.now(timezone(timedelta(hours=+9)))
        delta = (self.start_time - now).total_seconds()
        return delta if delta > 0 else 0.

    def get_state(self):
        now = datetime.now(timezone(timedelta(hours=+9)))
        if now < self.start_time:
            return 'before'
        elif now < self.end_time:
            return 'progress'
        else:
            return 'finished'

    def get_task_sample(self) -> Generator[Tuple[str, List[str], List[str]], None, None]:
        state = self.get_state()
        if state == 'before':
            print(f'{self.name} has not held yet.')
            return ()
        return ((name.lower(), *self.get_samples(url)) for name, url in self.get_tasks())

    def get_tasks(self) -> Generator[Tuple[str, str], None, None]:
        task_page = self.session.get(f'{self.url}/tasks').html
        task_anchors = task_page.xpath('//tr/td/a[contains(@href, "/tasks/")]')
        return ((a.text_content().strip(), urljoin(self.url, a.attrib['href'])) for a in task_anchors[::2])

    def get_samples(self, task_url: str) -> Tuple[List[str], List[str]]:
        html = self.session.get(task_url).html
        input_samps = [pre.text_content().strip().replace('\r\n', '\n')
                       for pre in html.xpath('//pre[contains(../h3/text(), "入力例")]')]
        output_samps = [pre.text_content().strip().replace('\r\n', '\n')
                        for pre in html.xpath('//pre[contains(../h3/text(), "出力例")]')]
        return (input_samps, output_samps)
