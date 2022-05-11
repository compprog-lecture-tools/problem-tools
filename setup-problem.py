#!/usr/bin/env python3
import argparse
import datetime
import json
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import jinja2
import questionary
from dateutil.relativedelta import relativedelta, TH

NOT_COURSES = {'tools'}
NOT_CONTESTS = {}
GIT_REPO_ROOT_CMD = ['git', 'rev-parse', '--show-toplevel']
TAGS = ['2-sat', 'binary search', 'bitmasks', 'brute force',
        'chinese remainder theorem', 'combinatorics', 'constructive algorithms',
        'data structures', 'dfs and similar', 'divide and conquer', 'dp', 'dsu',
        'expression parsing', 'fft', 'flows', 'games', 'geometry',
        'graph matchings', 'graphs', 'greedy', 'hashing', 'implementation',
        'math', 'matrices', 'meet-in-the-middle',
        'number theory', 'probabilities', 'schedules', 'shortest paths',
        'sortings', 'string suffix structures', 'strings', 'ternary search',
        'trees', 'two pointers']
DIFFICULTIES = ['[1] trivial', '[2] easy', '[3] medium', '[4] hard',
                '[5] very hard']


@dataclass
class ProblemJsonData:
    """Data to be saved to `problem.json`."""

    difficulty: int
    tags: List[str]
    description: str
    based_on_type: Optional[str] = None
    based_on_data: Optional[List[str]] = None


@dataclass
class ProblemInfo:
    """All information required to set up a problem."""

    course_dir: Path
    contest_dir: Path
    id: str
    solution_lang: str
    generator_lang: str
    answer_generator_lang: Optional[str]
    validator_lang: Optional[str]
    interactor: bool
    timelimit: int
    problem_json_data: ProblemJsonData

    @property
    def name(self):
        words = re.split(r'[\s\-_]+', self.id)
        return ' '.join(w.title() for w in words)

    @property
    def needs_testlib(self):
        return self.interactor or 'cpp' in (
            self.generator_lang, self.validator_lang)


def prompt_text(message, **kwargs):
    return questionary.text(message, **kwargs).unsafe_ask()


def prompt_select(message, choices, **kwargs):
    return questionary.select(message, choices, **kwargs).unsafe_ask()


def prompt_checkbox(message, choices, **kwargs):
    return questionary.checkbox(message, choices, **kwargs).unsafe_ask()


def prompt_confirm(message, **kwargs):
    return questionary.confirm(message, **kwargs).unsafe_ask()


def prompt_dir_or_new(directory, message, ignore):
    dirs = [e.name for e in directory.iterdir() if
            e.is_dir() and e.name not in ignore and not e.name.startswith('.')]
    dirs.append('*new*')
    dir_name = prompt_select(message, dirs)
    if dir_name == '*new*':
        dir_name = prompt_text('New directory name')
        (directory / dir_name).mkdir()
    return directory / dir_name


def prompt_language(message):
    return prompt_select(message, ['cpp', 'py'])


def validate_problem_id(problem_id):
    if 1 <= len(problem_id) <= 10:
        return True
    return 'Problem id should be at most 10 characters long'


def prompt_problem_json_data():
    difficulty_name = prompt_select('Difficulty', DIFFICULTIES)
    difficulty = DIFFICULTIES.index(difficulty_name) + 1
    tags = prompt_checkbox('Tags', TAGS)
    description = prompt_text('Description')
    data = ProblemJsonData(difficulty, tags, description)
    based_on_type = prompt_select('Based on',
                                  ['Nothing', 'Old problem', 'Codeforces',
                                   'Other'])
    if based_on_type == 'Old problem':
        old_course = prompt_text('Course of the old problem')
        old_contest = prompt_text('Contest of the old problem')
        old_name = prompt_text('Name of the old problem')
        data.based_on_type = 'old-problem'
        data.based_on_data = [old_course, old_contest, old_name]
    elif based_on_type == 'Codeforces':
        cf_contest = prompt_text('Id of the codeforces contest')
        cf_problem = prompt_text('Id of the codeforces problem')
        data.based_on_type = 'codeforces'
        data.based_on_data = [cf_contest, cf_problem]
    elif based_on_type == 'Other':
        data.based_on_type = 'other'
        data.based_on_data = [prompt_text('Based on text')]
    return data


def prompt_problem_info(repo_root, cwd):
    course_dir, contest_dir = None, None
    if cwd.parent == repo_root:
        course_dir = cwd
    elif cwd.parent.parent == repo_root:
        course_dir = cwd.parent
        contest_dir = cwd

    if course_dir is None:
        course_dir = prompt_dir_or_new(repo_root, 'Course directory',
                                       NOT_COURSES)
    else:
        print(f'Using course directory {course_dir.name}')
    if contest_dir is None:
        contest_dir = prompt_dir_or_new(course_dir, 'Contest directory',
                                        NOT_CONTESTS)
        contest_makefile = contest_dir / 'Makefile'
        if not contest_makefile.exists():
            contest_makefile.symlink_to('../../tools/make/ContestMakefile')
    else:
        print(f'Using contest directory {contest_dir.name}')

    problem_id = prompt_text('Problem id', validate=validate_problem_id)
    solution_lang = prompt_language('Solution language')
    generator_lang = prompt_language('Generator language')

    answer_generator_lang = None
    interactor = False
    validator_lang = None
    if prompt_confirm('Add interactor', default=False):
        # Interactor implies an answer generator but no validator
        interactor = True
        answer_generator_lang = prompt_language('Answer generator language')
    elif prompt_confirm('Add validator', default=False):
        validator_lang = prompt_language('Validator language')
        if prompt_confirm('Add answer generator'):
            answer_generator_lang = prompt_language('Answer generator language')
    timelimit = prompt_text('Timelimit', default='1.0')
    problem_json_data = prompt_problem_json_data()
    return ProblemInfo(course_dir, contest_dir, problem_id, solution_lang,
                       generator_lang, answer_generator_lang, validator_lang,
                       interactor, timelimit, problem_json_data)


def setup_jinja_env(repo_root, course_directory):
    loader = jinja2.PrefixLoader(delimiter=':', mapping={
        'global': jinja2.FileSystemLoader(
            str(repo_root / 'tools/make/templates')),
        'repo': jinja2.FileSystemLoader(str(repo_root / '.template'))
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


def save_problem_json(data, problem_dir):
    with (problem_dir / 'problem.json').open('w') as f:
        json_data = {
            'description': data.description,
            'difficulty': data.difficulty,
            'tags': data.tags,
        }
        if data.based_on_type is not None:
            json_data['based_on'] = {
                'type': data.based_on_type,
                'data': data.based_on_data,
            }
        json.dump(json_data, f, indent=2, sort_keys=True)


def setup_problem(info, repo_root):
    jinja_env = setup_jinja_env(repo_root, info.course_dir)
    problem_dir = info.contest_dir / info.id
    problem_dir.mkdir()

    render_template(jinja_env, 'repo:problem.tex', 
                    problem_dir / 'problem.tex') # TODO this could be a simple copy
    render_template(jinja_env, 'repo:notes.ipe', problem_dir / 'notes.ipe',
                    problem_name=info.name)

    executables_dir = problem_dir / 'executables'
    executables_dir.mkdir()
    seed = random.randrange(-2 ** 63, 2 ** 63)
    setup_executable('solution', info.solution_lang, executables_dir, jinja_env)
    setup_executable('generator', info.generator_lang, executables_dir,
                     jinja_env, seed=seed)
    if info.validator_lang is not None:
        setup_executable('validator', info.validator_lang, executables_dir,
                         jinja_env)
    if info.answer_generator_lang is not None:
        setup_executable('answer-generator', info.answer_generator_lang,
                         executables_dir, jinja_env)
    if info.interactor:
        setup_executable('interactor', 'cpp', executables_dir, jinja_env)

    if info.needs_testlib:
        (executables_dir / 'testlib.h').symlink_to(
            '../../../../tools/make/testlib.h')

    (problem_dir / 'domjudge-problem.ini').write_text(
        f'timelimit={info.timelimit}\n')
    (problem_dir / 'Makefile').symlink_to('../../../tools/make/Makefile')
    save_problem_json(info.problem_json_data, problem_dir)


def upgrade_problem(cwd, repo_root):
    problem_dir = None
    try:
        index = cwd.parents.index(repo_root)
        if index == 2:
            problem_dir = cwd
        elif index > 2:
            problem_dir = cwd.parents[index - 3]
    except ValueError:
        pass
    if problem_dir is None:
        print('Upgrade must be run from inside a problem directory',
              file=sys.stderr)
        sys.exit(1)

    with (problem_dir / 'domjudge-problem.ini').open() as f:
        if sum(1 for line in f if line.strip() != '') > 1:
            print('Problem ini contains more than just timelimit. '
                  'Check manually.')

    try:
        with (problem_dir / 'problem.json').open() as f:
            data = json.load(f)
    except FileNotFoundError:
        print('Problem.json missing, upgrading')
        problem_json_data = prompt_problem_json_data()
        save_problem_json(problem_json_data, problem_dir)
    else:
        if 'description' not in data:
            print('Problem description missing')
            data['description'] = prompt_text('Description')
            with (problem_dir / 'problem.json').open('w') as f:
                json.dump(data, f, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description='Setup or upgrade a problem')
    parser.add_argument('-u', '--upgrade', action='store_true',
                        help='Upgrade an existing problem instead of creating '
                             'a new one')
    args = parser.parse_args()

    repo_root = Path(
        subprocess.check_output(GIT_REPO_ROOT_CMD).rstrip().decode('utf-8'))
    cwd = Path.cwd()
    if args.upgrade:
        upgrade_problem(cwd, repo_root)
    else:
        info = prompt_problem_info(repo_root, cwd)
        setup_problem(info, repo_root)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
