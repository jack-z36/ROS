# Stage 4 Acceptance Modes

Use this reference when an L3 acceptance card's mode or conclusion needs interpretation.

## Modes

| Mode | Meaning | Required action |
|---|---|---|
| `direct-local` | The L3 can be checked locally on Ubuntu 22.04 without hardware. | Run the command in the card or L3 file. Record stdout/log observations. |
| `static-review` | The L3 is best checked by diff, interface, and boundary review. | Check execution summary, allowed/forbidden files, API contracts, and rollback. |
| `downstream-l2` | The L3 contributes to a later L3 or L2 runtime scenario but has no standalone closure. | Confirm contribution and identify the downstream L3/L2 scenario that proves runtime behavior. |
| `hardware-blocked` | Real validation requires robot, gripper, SDK, sensors, or physical safety setup. | Review code and risk only. Keep real hardware result blocked. |
| `env-blocked` | The check is local in principle but the Ubuntu environment lacks ROS, bundle, dependency, or SDK. | Record the missing environment item. Do not mark pass or fail. |

## Conclusions

| Conclusion | Meaning |
|---|---|
| `PASS_LOCAL` | The local or static acceptance expected for this card passed. |
| `FAIL_LOCAL` | A local command, static review item, or boundary rule failed and must be fixed. |
| `BLOCKED_ENV` | Required non-hardware environment dependency is missing. |
| `BLOCKED_HARDWARE_EXPECTED` | Real hardware validation is impossible in the no-hardware environment and is correctly blocked. |
| `DEFER_TO_L2_GATE` | The L3 was reviewed but full behavior must be proved by a downstream L3 or L2 Gate. |

## Hard Rules

- Never mark real-robot behavior as passed without hardware.
- Do not fail a task only because hardware is absent when its card expects `hardware-blocked`.
- Do fail a task if it silently claims hardware success under no-hardware conditions.
- Do fail a task if it modifies files outside the L3 allowed scope.
- Do fail a task if it lacks an execution summary after implementation.
