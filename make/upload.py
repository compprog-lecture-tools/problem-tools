#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
import dateutil.parser
import questionary
import requests
import toml
import yaml
from lxml import html
from requests.auth import HTTPBasicAuth
from typing import List, Optional


def exit_error(message):
    print(f'-> {message}')
    sys.exit(1)


def name_by_filename(filename):
    return os.path.splitext(os.path.basename(filename))[0]


def get_login_entries():
    path = Path(__file__).resolve().parents[2] / 'login.toml'
    try:
        with open(path, 'r') as f:
            return toml.load(f)
    except OSError as err:
        exit_error(f'login.toml not found or not accessible:\n\n{err}')


def get_team_categories(base_url, session):
    response = session.get(base_url + '/jury/categories')
    tree = html.document_fromstring(response.content)
    table_rows = tree.xpath(f"//tbody/tr")[0]
    
    categories = []
    for i, n in zip(table_rows.xpath('//td[1]/a/text()'), table_rows.xpath('//td[4]/a/text()')):

        categories.append({
            'id': i.strip(),
            'name': n.strip()
        })

    return categories


def is_contest(contest, only_testing=False, also_future=True):
    now = datetime.now(timezone.utc)
    if 'start_time' not in contest or contest['start_time'] is None or 'end_time' not in contest or contest['end_time'] is None:
        return False

    start_time = dateutil.parser.parse(contest['start_time'])
    end_time = dateutil.parser.parse(contest['end_time'])
    shortname = contest['shortname']
    return (shortname.endswith('testing') or not only_testing) and (start_time <= now or also_future) and now <= end_time


def get_contest(base_url, auth, only_testing=False, also_future=True):
    data = requests.get(f'{base_url}/api/v4/contests', auth=auth).json()
    return [
        contest for contest in data
        if is_contest(contest, only_testing=only_testing, also_future=also_future)
    ]


def problem_id_by_name(session, base_url, problem_name):
    response = session.get(base_url + '/jury/problems')
    tree = html.document_fromstring(response.content)
    problem_links = tree.xpath(
        f"//table/tbody/tr/td/a[contains(text(), '{problem_name}')]/@href")
    if problem_links:
        return name_by_filename(problem_links[0])
    return False


def problem_on_judge(session, base_url, problem_name):
    return problem_id_by_name(session, base_url, problem_name) is not False


def delete_problem(session, base_url, problem_name):
    problem_id = problem_id_by_name(session, base_url, problem_name)

    session.post(f'{base_url}/jury/problems/{problem_id}/delete')

    if problem_on_judge(session, base_url, problem_name):
        exit_error(f'Deleting the problem {problem_name} did not work!')

    print('-> Problem deleted successfully')


def upload_problem(base_url, auth, contest_id, filename):
    upload_response = requests.post(
        f'{base_url}/api/v4/contests/{contest_id}/problems',
        files={'zip': open(filename, 'rb')},
        auth=auth
    )

    if 'Saved problem' in upload_response.text:
        return True
    return upload_response.status_code


def link_problem(base_url, auth, session, contest_id, problem_name):
    problem_id = problem_id_by_name(session, base_url, problem_name)

    if problem_id is False:
        exit_error('trying to link nonexistant problem')

    response = requests.put(
        f'{base_url}/api/v4/contests/{contest_id}/problems/{problem_id}', auth=auth, data={'label': problem_name, })

    if response.status_code != 200:
        if 'already linked' not in str(response.content):
            exit_error(
                f'linking problem {problem_name} failed with code {response.status_code}\n {response.content}'
                )

    print(f'-> problem {problem_name} linked successfully')


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


def validator_on_judge(session, base_url, validator_name):
    response = session.get(f'{base_url}/jury/executables/{validator_name}')

    return response.status_code == 200


def delete_validator(session, base_url, validator_name):
    session.post(f'{base_url}/jury/executables/{validator_name}/delete')
    if validator_on_judge(session, base_url, validator_name):
        exit_error(f'Deleting the Executable {validator_name} did not work!')

    print('-> Validator deleted successfully')


def upload_validator(session, base_url, filename):
    data = {'executable_upload[type]': 'compare'}
    files = {'executable_upload[archives][]': open(filename, 'rb')}
    upload_response = session.post(
        base_url + '/jury/executables/add', data, files=files)
    return upload_response.status_code


def prompt_choice(message, choices):
    return questionary.select(message=message, choices=choices).unsafe_ask()


def create_contest(base_url, auth, session):
    contest = {
        'contest[starttimeEnabled]': 1,
        'contest[freezetimeString]': '',
        'contest[unfreezetimeString]': '',
        'contest[deactivatetimeString]': '',
        'contest[allowSubmit]': 1,
        'contest[processBalloons]': 0,
        'contest[runtimeAsScoreTiebreaker]': 1,
        'contest[medalsEnabled]': 0,
        'contest[goldMedals]': 4,
        'contest[silverMedals]': 4,
        'contest[bronzeMedals]': 4,
        'contest[public]': 0,
        'contest[openToAllTeams]': 0,
        'contest[enabled]': 1
    }

    contest['contest[shortname]'] = questionary.text(
        'Short name:').unsafe_ask()
    contest['contest[name]'] = questionary.text(
        'Name:', default=contest['contest[shortname]']).unsafe_ask()
    start_time = questionary.text(
        'Start time:', default=datetime.now().strftime('%d.%m.%y %H:%M')).unsafe_ask()

    try:
        start_time = datetime.strptime(start_time, '%d.%m.%y %H:%M')
        contest['contest[starttimeString]'] = start_time.strftime(
            '%Y-%m-%d %H:%M:00 Europe/Berlin')
    except:
        exit_error('Wrong format! (%d.%m.%y %H:%M)')

    end_time = questionary.text('End time:', default=(
        datetime.now() + timedelta(weeks=1)).strftime('%d.%m.%y %H:%M')).unsafe_ask()

    try:
        end_time = datetime.strptime(end_time, '%d.%m.%y %H:%M')
        contest['contest[endtimeString]'] = end_time.strftime(
            '%Y-%m-%d %H:%M:00 Europe/Berlin')
    except:
        exit_error('Wrong format! (%d.%m.%y %H:%M)')

    categories = get_team_categories(base_url, session)
    if contest['contest[shortname]'].endswith('testing'):
        category_id = [category['id'] for category in categories if category['name'] == 'Staff']
        print('Using category Staff for testing contest')
    else:
        category_id = questionary.select('Which category to add', [
            questionary.Choice(title=category['name'], value=category['id'])
            for category in categories
        ]).unsafe_ask()

    contest['contest[teamCategories][]'] = category_id
    contest['contest[activatetimeString]'] = contest['contest[starttimeString]']

    response = session.post(f'{base_url}/jury/contests/add', data=contest)

    if response.status_code != 200:
        exit_error(f'failed with status code {response.status_code}')

    contests = requests.get(f'{base_url}/api/v4/contests', auth=auth).json()
    contest_id = [c['id'] for c in contests if c['shortname']
                  == contest['contest[shortname]']][0]

    return contest_id


def get_judge_data():
    judges = get_login_entries()
    if any('contests' in judge for judge in judges.values()):
        print('login.toml contains contest list which is no longer needed')

    if len(judges) == 1:
        base_url = list(judges.keys())[0]
        print(f'Uploading to {base_url}')
    else:
        base_url = prompt_choice('Where to upload to', judges.keys())

    username = judges[base_url]['username']
    password = judges[base_url].get('password')
    if not password:
        password = questionary.password(message='Judge password').unsafe_ask()

    if base_url[-1] == '/':
        base_url = base_url[:-1]

    auth = HTTPBasicAuth(username, password)
    session = requests.Session()
    # auth is used for api requests and the logged in session is needed for calls that are not supported by the api

    csrf_token = get_csrf_token(session, base_url)
    if not login(session, base_url, csrf_token, username, password):
        exit_error('Invalid login data')

    return base_url, auth, session


def get_contest_id(base_url, auth, session):
    contests = get_contest(base_url, auth)
    if not contests:
        exit_error(
            'No running testing contests found for judge (shortname must end in "testing")')

    contest_id = prompt_choice('Which contest to add to', [
        questionary.Choice(title=contest['shortname'], value=contest['id'])
        for contest in contests
    ] + ['*new*'])

    if contest_id == '*new*':
        contest_id = create_contest(base_url, auth, session)

    return contest_id


def upload_problem_main(base_url, auth, session, problem_zip, validator_zip, contest_id=None):
    if contest_id is None:
        contest_id = get_contest_id(base_url, auth, session)

    if validator_zip is not None:
        # Upload the validator first, so that the problem can be linked to it
        # using its domjudge-problem.ini

        validator_name = name_by_filename(validator_zip)
        if validator_on_judge(session, base_url, validator_name):
            if questionary.confirm(
                    'Validator already exists. Delete and reupload?').unsafe_ask():
                delete_validator(session, base_url, validator_name)

        if not validator_on_judge(session, base_url, validator_name):
            result = upload_validator(session, base_url, validator_zip)
            if result == 200:
                print('-> Validator uploaded successfully')
            else:
                exit_error(
                    f'Validator upload failed with status code {result}')

    if problem_zip is not None:
        problem_name = name_by_filename(problem_zip)
        if problem_on_judge(session, base_url, problem_name):
            if not questionary.confirm(
                    'Problem already exists. Delete and reupload?').unsafe_ask():
                link_problem(base_url, auth, session, contest_id, problem_name)
                return

            delete_problem(session, base_url, problem_name)

        result = upload_problem(base_url, auth, contest_id, problem_zip)
        if result is True:
            print('-> Problem uploaded successfully')
        else:
            exit_error(f'Problem upload failed with status code {result}')


def upload_contest_main(base_url, auth, session):
    contest_id = get_contest_id(base_url, auth, session)

    problem_paths = [f.path for f in os.scandir('.') if f.is_dir()]
    for problem_path in problem_paths:
        problem_zip = os.path.join(
            problem_path, 'build', f'{os.path.basename(problem_path)}.zip')
        if not os.path.exists(problem_zip):
            exit_error(f'{problem_zip} does not exist!')

        validator_zip = os.path.join(
            problem_path, 'build', f'{os.path.basename(problem_path)}-validator.zip')
        if not os.path.exists(validator_zip):
            validator_zip = None

        print()
        print(f'-> Uploading problem {os.path.basename(problem_path)}')
        upload_problem_main(base_url, auth, session, problem_zip,
                            validator_zip, contest_id=contest_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--problem-zip', '-p',
                        help='the filename of a problem to upload')
    parser.add_argument('--validator-zip', '-v',
                        help='the filename of a validator zip to upload')
    parser.add_argument('--contest', '-c', action='store_true',
                        help='upload a contest?')

    args = parser.parse_args()

    if args.contest != (args.problem_zip is None and args.validator_zip is None):
        exit_error('Specify either contest or problem data')

    base_url, auth, session = get_judge_data()

    if args.contest:
        upload_contest_main(base_url, auth, session)
    else:
        upload_problem_main(base_url, auth, session,
                            args.problem_zip, args.validator_zip)


if __name__ == '__main__':
    try:
        main()
    except requests.ConnectionError:
        exit_error('Server cannot be accessed')
    except KeyboardInterrupt:
        pass
