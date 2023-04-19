#!/usr/bin/env python3
import sys
from datetime import datetime, timezone
from pathlib import Path

import dateutil.parser
import questionary
import requests
import toml
from lxml import html
from requests.auth import HTTPBasicAuth


def exit_error(message):
    print(f'-> {message}')
    sys.exit(1)


def get_login_entries():
    path = Path(__file__).resolve().parents[2] / 'login.toml'
    try:
        with open(path, 'r') as f:
            return toml.load(f)
    except OSError as err:
        exit_error(f'login.toml not found or not accessible:\n\n{err}')


def is_active_testing_contest(contest):
    now = datetime.now(timezone.utc)
    start_time = dateutil.parser.parse(contest['start_time'])
    end_time = dateutil.parser.parse(contest['end_time'])
    shortname = contest['shortname']
    return shortname.endswith('testing') and start_time <= now <= end_time


def get_active_testing_contest(base_url, auth):
    data = requests.get(f'{base_url}/api/v4/contests', auth=auth).json()
    return [
        contest for contest in data
        if is_active_testing_contest(contest)
    ]


def upload_problem(base_url, auth, contest_id, filename):
    upload_response = requests.post(
        f'{base_url}/api/v4/contests/{contest_id}/problems',
        files={'zip': open(filename, 'rb')},
        auth=auth
    )

    if 'Saved problem' in upload_response.text:
        return True
    return upload_response.status_code


def get_csrf_token(session, base_url):
    csrf_response = session.get(base_url + '/login')
    tree = html.document_fromstring(csrf_response.content)
    return tree.xpath("//input[contains(@name, '_csrf_token')]")[0].value


def login(session, base_url, csrf_token, username, password):
    data = {
        '_username': username,
        '_password': password,
        '_csrf_token': csrf_token
    }
    login_response = session.post(base_url + '/login', data)
    # Successful login will redirect somewhere else, unsuccessful stays on
    # login page
    return 'login' not in login_response.url


def upload_validator(session, base_url, filename):
    data = {'executable_upload[type]': 'compare'}
    files = {'executable_upload[archives][]': open(filename, 'rb')}
    upload_response = session.post(base_url + '/jury/executables/add',
                                   data,
                                   files=files)
    return upload_response.status_code


def prompt_choice(message, choices):
    return questionary.select(message=message, choices=choices).unsafe_ask()


def main():
    judges = get_login_entries()
    if any('contests' in judge for judge in judges.values()):
        print('login.toml contains contest list which is no longer needed')
    base_url = prompt_choice('Where to upload to', judges.keys())
    username = judges[base_url]['username']
    password = judges[base_url].get('password')

    auth = HTTPBasicAuth(username, password)

    if base_url[-1] == '/':
        base_url = base_url[:-1]

    if not password:
        password = questionary.password(message='Judge password').unsafe_ask()

    contests = get_active_testing_contest(base_url, auth)
    if not contests:
        exit_error('No running testing contests found for judge '
                   '(shortname must end in "testing")')

    contest_id = prompt_choice('Which contest to add to', [
        questionary.Choice(title=contest['shortname'], value=contest['id'])
        for contest in contests
    ])

    if len(sys.argv) == 3:
        # Upload the validator first, so that the problem can be linked to it
        # using its domjudge-problem.ini

        session = requests.Session()
        csrf_token = get_csrf_token(session, base_url)
        if not login(session, base_url, csrf_token, username, password):
            exit_error('Invalid login data')

        result = upload_validator(session, base_url, sys.argv[2])
        if result == 200:
            print('-> Validator uploaded successfully')
        elif result == 500:
            # We get a 500 code with lots of SQL code if the problem already
            # exists
            exit_error('Validator upload failed, maybe it was uploaded before')
        else:
            exit_error(f'Validator upload failed with status code {result}')

    result = upload_problem(base_url, auth, contest_id, sys.argv[1])
    if result is True:
        print('-> Problem uploaded successfully')
    elif result == 200:
        # If the problem already exists, we still get 200 as a response
        exit_error('-> Problem upload failed, maybe it was uploaded before')
    else:
        exit_error(f'Problem upload failed with status code {result}')


if __name__ == '__main__':
    try:
        main()
    except requests.ConnectionError:
        exit_error('Server cannot be accessed')
    except KeyboardInterrupt:
        pass
