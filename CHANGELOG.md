## v0.3.0

### ⬆️ Update dependencies

* Provide support for `aiida-core~=2.7` via `BashCliScheduler` [[42b8f14](https://github.com/aiidateam/aiida-hyperqueue/commit/42b8f14412121daddc0a2e9eea1360ad949d4e65)]

## v0.2.1

### 🔧 Maintenance

* Add `update_changelog.py` script [[9b03acb](https://github.com/aiidateam/aiida-hyperqueue/commit/9b03acbf9cb804ef7f3c35c6d5b7495b917dacc6)]
* Add upper limit to `aiida-core` [[fd7a62f](https://github.com/aiidateam/aiida-hyperqueue/commit/fd7a62feae23f99899a025cfe411531576bf93fd)]

## v0.2.0

- [#18](https://github.com/aiidateam/aiida-hyperqueue/pull/18) A large refactoring with following changes:

    - correctly support memory setup for resources.
    - support turn on hyperthreading with latest version of hyperqueue.
    - Support install hq to remote computer over CLI.
    - adding unit tests with submit to real hq using the fixture from hyperqueue repo.
    - Fix the submit bug for hq > 0.12 that resources are configured twice in job script and submit command.

- [#26](https://github.com/aiidateam/aiida-hyperqueue/pull/26) Change alloc add worker name (name appear in slurm queue) `aiida` -> `ahq`
- [#24](https://github.com/aiidateam/aiida-hyperqueue/pull/24) Use JSON format as output for hq job list and hq submit

## v0.1.1

Only a small fix to the `README.md` was added here, this release is mainly to test the automated deployment to PyPI.

## v0.1.0

First release on PyPI, tested with HyperQueue v0.15.0.
