#!/usr/bin/env python3
import datetime
import random
import re
import subprocess
from pathlib import Path

import jinja2
import questionary
from dateutil.relativedelta import relativedelta, FR

NOT_COURSES = {'tools'}
NOT_CONTESTS = {'templates'}
GIT_REPO_ROOT_CMD = ['git', 'rev-parse', '--show-toplevel']


def prompt_single(prompt_type, **kwargs):
    return questionary.prompts.prompt_by_name(prompt_type)(**kwargs).unsafe_ask()


def select_dir_or_new(directory, message, ignore):
    dirs = [e.name for e in directory.iterdir() if
            e.is_dir() and e.name not in ignore and not e.name.startswith('.')]
    dirs.append('*new*')
    dir_name = prompt_single('list', message=message, choices=dirs)
    if dir_name == '*new*':
        dir_name = prompt_single('input', message='New directory name')
        (directory / dir_name).mkdir()
    return directory / dir_name


def to_problem_name(problem_id):
    words = re.split(r'[\s\-_]+', problem_id)
    return ' '.join(w.title() for w in words)


def prompt_language(message):
    return prompt_single('list', message=message, choices=['cpp', 'py'])


def prompt_submission_date():
    today = datetime.date.today()
    friday = today + relativedelta(weekday=FR)
    is_friday = today == friday
    fridays = {}
    if not is_friday:
        fridays[f'This friday ({friday:%d.%m.%Y})'] = friday
    for i in range(4):
        friday += relativedelta(weeks=1)
        desc = 'Next friday' if i == 0 else f'Friday in {i + 1} weeks'
        fridays[f'{desc} ({friday:%d.%m.%Y})'] = friday
    choices = list(fridays.keys()) + ['*other*']
    choice = prompt_single('list', message='Submission date', choices=choices)
    if choice == '*other*':
        return prompt_single('input', message='Custom submission date')
    return f'{fridays[choice]:%d.%m.%Y}'


def setup_jinja_env(repo_root, course_directory):
    loader = jinja2.PrefixLoader(delimiter=':', mapping={
        'global': jinja2.FileSystemLoader(str(repo_root / 'tools/make/templates')),
        'course': jinja2.FileSystemLoader(str(course_directory / 'templates'))
    })
    return jinja2.Environment(
        loader=loader,
        # Default {{ and }} doesn't work nicely with LaTeX syntax
        variable_start_string='{@',
        variable_end_string='@}',
    )


def render_template(jinja_env, template_name, to, **kwargs):
    template = jinja_env.get_template(template_name)
    Path(to).write_text(template.render(**kwargs))


def setup_executable(name, language, executables_dir, jinja_env, **kwargs):
    file_name = f'{name}.{language}'
    render_template(jinja_env, f'global:{file_name}',
                    executables_dir / file_name, **kwargs)


def validate_problem_id(problem_id):
    if 1 <= len(problem_id) <= 10:
        return True
    return 'Problem id should be at most 10 characters long'


def main():
    repo_root = Path(
        subprocess.check_output(GIT_REPO_ROOT_CMD).rstrip().decode('utf-8'))
    cwd = Path.cwd()
    course_dir, contest_dir = None, None
    if cwd.parent == repo_root:
        course_dir = cwd
    elif cwd.parent.parent == repo_root:
        course_dir = cwd.parent
        contest_dir = cwd

    if course_dir is None:
        course_dir = select_dir_or_new(repo_root, 'Course directory',
                                       NOT_COURSES)
    else:
        print(f'Using course directory {course_dir.name}')
    if contest_dir is None:
        contest_dir = select_dir_or_new(course_dir, 'Contest directory',
                                        NOT_CONTESTS)
        contest_makefile = contest_dir / 'Makefile'
        if not contest_makefile.exists():
            contest_makefile.symlink_to('../../tools/make/ContestMakefile')
    else:
        print(f'Using contest directory {contest_dir.name}')

    problem_id = prompt_single('input', message='Problem id',
                               validate=validate_problem_id)
    problem_name = to_problem_name(problem_id)
    solution_lang = prompt_language('Solution language')
    generator_lang = prompt_language('Generator language')
    validator_lang = None
    if prompt_single('confirm', message='Add validator', default=False):
        validator_lang = prompt_language('Validator language')

    if prompt_single('confirm', message='Is live contest?', default=False):
        submission_date = 'end of'
        submission_time = 'contest'
    else:
        submission_date = prompt_submission_date()
        submission_time = prompt_single('input', message='Submission time',
                                        default='13:30')
    timelimit = prompt_single('input', message='Timelimit', default='1.0')

    jinja_env = setup_jinja_env(repo_root, course_dir)
    problem_dir = contest_dir / problem_id
    problem_dir.mkdir()

    render_template(jinja_env, 'course:description/problem.tex',
                    problem_dir / 'problem.tex', submission_date=submission_date,
                    submission_time=submission_time)
    (problem_dir / '.template').symlink_to(
        '../../templates/description/template', target_is_directory=True)
    render_template(jinja_env, 'course:notes.ipe', problem_dir / 'notes.ipe',
                    problem_name=problem_name)

    executables_dir = problem_dir / 'executables'
    executables_dir.mkdir()
    seed = random.randrange(-2 ** 63, 2 ** 63)
    setup_executable('solution', solution_lang, executables_dir, jinja_env)
    setup_executable('generator', generator_lang, executables_dir, jinja_env,
                     seed=seed)
    if validator_lang is not None:
        setup_executable('validator', validator_lang, executables_dir,
                         jinja_env)
    if 'cpp' in (generator_lang, validator_lang):
        (executables_dir / 'testlib.h').symlink_to('../../../../tools/make/testlib.h')

    (problem_dir / 'domjudge-problem.ini').write_text(f'timelimit={timelimit}\n')
    (problem_dir / 'Makefile').symlink_to('../../../tools/make/Makefile')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
