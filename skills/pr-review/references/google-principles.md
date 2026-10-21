# Google code review principles

Canonical source: [Google eng-practices](https://google.github.io/eng-practices/review/). This reference holds the ten principles the canon reviews grade against, plus the priority order used by ranking, plus when each principle applies. Vendored here so this skill is self-contained.

## Priority order

Google's own emphasis order ("the most important thing to cover in a review is the overall design of the CL") — context for calibrating how much a finding matters, most important first:

1. design
2. complexity
3. tests
4. functionality
5. naming
6. comments
7. documentation
8. every-line
9. consistency
10. style

The order is not a filter — every principle is first-class.

## Code-health framing

Quote from `reviewer/standard.html`: "In general, reviewers should favor approving a CL once it is in a state where it definitely improves the overall code health of the system being worked on, even if the CL isn't perfect."

Every finding's `why` traces to code health. The principles below are facets of code health, not preferences. When a finding cannot be grounded in one of them, the finding is wrong and is dropped.

## 1. Design

Quote from `reviewer/looking-for.html`: "The most important thing to cover in a review is the overall design of the CL."

A `design` finding is filed when:

- The change does not fit the codebase or the library it lives in.
- The change introduces a system boundary that should not exist, or crosses a boundary it should not.
- The change adds a dependency or coupling that complicates future change.
- The timing of the change is wrong (e.g., adds API surface that the system is not ready to support).
- Multiple unrelated concerns share one function or one type.

Cheapest evidence: the change's location in the file tree. A new feature in a package that does not own that concern is a design finding even before the code is read.

## 2. Complexity

Quote from `reviewer/looking-for.html`: "Is the CL more complex than it should be? ... Developers are likely to introduce bugs when they try to call or modify this code."

A `complexity` finding is filed when:

- A function does more work than its name implies.
- A class hierarchy or interface set adds layers without a present consumer that benefits.
- Speculative generality (parameters, generics, hooks) appears with no current second use.
- Control flow nests deeper than the problem requires.
- A clever construct replaces a plain one without measurable benefit.

Cheapest evidence: cyclomatic complexity of the changed function; presence of `<T, U, V>` style generics with only one instantiation; switch arms or branches that handle cases the API never produces.

## 3. Tests

Quote from `reviewer/looking-for.html`: "Tests should be of high quality and reasonable. Tests should be designed in a way that they actually fail when the code is broken."

A `tests` finding is filed when:

- A code path that affects behavior has no test.
- A test asserts on incidental output (timestamps, ordering of unordered iteration) and would pass even when the code is broken.
- A test mocks the unit under test, leaving only the mocks tested.
- A test is fragile: depends on test order, shared mutable state, or wall-clock time.
- Test names describe the inputs, not the contract being verified.

Cheapest evidence: in the diff, is there test coverage for each new branch or behavior? Do the tests assert on behavior or on implementation details?

## 4. Functionality

Quote from `reviewer/looking-for.html`: "Does this CL do what the developer intended? ... think about edge cases, think about concurrency problems."

A `functionality` finding is filed when:

- An edge case the change touches is unhandled (empty input, max value, nil, off-by-one).
- A concurrency change introduces a race, deadlock, or lost wakeup.
- A UI change degrades a use case the change did not intend to touch.
- The change's stated intent and its observable behavior diverge.

`functionality` is not bug-hunting-with-confidence-scoring. The `why` must trace to a code-health concern (this edge case is unhandled, this concurrency contract is broken), not "this might fail at runtime sometime maybe."

## 5. Naming

Quote from `reviewer/looking-for.html`: "Did the developer pick good names? A good name is long enough to fully communicate what the item is or does, without being so long that it becomes hard to read."

A `naming` finding is filed when:

- A name does not communicate what the thing is or does.
- A name is so short that the reader must guess the meaning from context.
- A name is so long that it becomes hard to read.
- A name overlaps with a sibling name to the point that the two are easily confused.
- A name re-uses a term already used in the codebase for a different concept.

## 6. Comments

Quote from `reviewer/looking-for.html`: "Comments should be clear and useful, and mostly explain why instead of what."

A `comments` finding is filed when:

- A comment describes what the code does, not why.
- A comment is stale and contradicts the code it sits next to.
- A non-obvious decision (a constraint, an invariant, a workaround) is not commented.
- A public API has no doc comment, or its doc comment does not state purpose, usage, and behavior.

The default is no comment. A comment is only a praise candidate when it surfaces a why that the code itself cannot express.

## 7. Documentation

Quote from `reviewer/looking-for.html`: "If a CL changes how users build, test, interact with, or release code, check to see that it updates associated documentation."

A `documentation` finding is filed when:

- A change to build, test, or release flow does not update the README or the relevant doc.
- A deprecated API's documentation is not removed.
- A public protocol or contract changes without a doc update.

The review never writes the docs. When the missing doc is substantive, file the finding and name the doc that needs updating.

## 8. Every-line

Quote from `reviewer/looking-for.html`: "In general, look at every line of code that you have been assigned to review."

An `every-line` finding is filed when:

- A line of code is unclear and the reviewer cannot determine what it does.
- A specialty area (security, privacy, concurrency, performance) needs a qualified reviewer beyond this pass.
- Generated or vendored code is mixed with human-written code in a way that makes review harder.

`every-line` is also the catch-all for code that warrants comment but does not fit another principle. Use sparingly.

## 9. Consistency

Quote from `reviewer/looking-for.html`: "Try to keep new code consistent with existing code. ... However, in some cases, the existing code is inconsistent or wrong."

A `consistency` finding is filed when:

- New code introduces a pattern that differs from the established one in the same package, with no stated reason.
- The change converts some callsites to a new pattern but leaves others unconverted, creating two patterns where one existed.

Consistency defers to repository style guides when present. When the style guide explicitly allows the new pattern, the finding is wrong.

## 10. Style

Quote from `reviewer/looking-for.html`: "Make sure the CL follows the appropriate style guides. ... If the only thing wrong with the code is that the author isn't following the style guide, prefix your comment with 'Nit:'."

A `style` finding is filed when:

- The change violates the project's style guide in a way the linter does not catch.
- The change mixes a large reformat with functional changes, making the functional changes hard to review.

The canon review does not re-implement a linter. File a `style` finding only when the choice degrades readability beyond what the linter mechanically flags. Pure style issues default to the lowest severity.

## Triage-only concerns

These three never become table findings — they belong in the canon review's Triage notes prose block:

- **small-cl** — sourced from `developer/small-cls.html`. Should this change be split? Pressure scales with size and with how many unrelated concerns the diff mixes.
- **description** — sourced from `developer/cl-descriptions.html`. Does the stated intent (PR description, linked issues) say what changed and why, at a level a future reader can act on?
- **specialty** — advisory only: security, privacy, concurrency, or performance surface area that deserves a qualified human reviewer beyond this pass.
