# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-01

### Added

- `simulate_onchange_create` helper for the Odoo `new()` → onchange → `create()` pattern.
- `WorkflowScenarioMixin` with `run_workflow_steps()` for YAML-driven workflow tests.
- `PolicyScenarioMixin` with `assert_policies()` for YAML-driven policy tests.
- `OdooScenarioMixin` combining both mixins.
- Convenience re-exports of `ddt`, `data`, `file_data`, `unpack` from the `ddt` package.
