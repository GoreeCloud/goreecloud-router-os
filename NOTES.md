# GoreeCloud Router OS — Development Notes

## Current engineering decision boundary

The core production implementation language has **not** been selected in the authoritative Router OS specification. The Milestone 0 proof is implemented in Python only to make the state/validation/transaction design executable and testable without committing the product to Python as its privileged runtime language.

## Safety boundary

No current source file is allowed to mutate host networking. A future privileged adapter must be introduced as a separate reviewed change with explicit command allowlisting, structured arguments, preflight validation, rollback behavior, and virtual-machine acceptance tests.

## Repository bootstrap

The initial repository was created empty. The first direct `main` commit exists only to establish the otherwise-unborn default branch so subsequent material work can use a development branch and pull request.

## Documentation synchronization

`FEATURE-ROADMAP.md` and `USER-MANUAL.md` are paired with their central GoreeCloud Drive counterparts. Planned features remain distinguished from implemented prototype behavior.
