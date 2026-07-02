---
tags:
  - program-principle
  - pi05-vla
  - control-loop
  - annotation
source_note: "01-doing/pi05_test/learning/deploy-inference-dataflow"
source_code: "01-doing/pi05_test/pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py"
concept: "ControlLoop.tick"
---

# ControlLoop.tick annotations

## 1. What `tick()` is

`ControlLoop.tick()` is the high-frequency scheduling step of the Pi0.5 VLA deployment runtime.

It is called by the ROS2 timer at `control_hz`, normally 30 Hz. Each call tries to return exactly one safe robot command without blocking on model inference.

In the deployment dataflow, `tick()` corresponds to the control-plane node:

```text
D08 Control loop scheduling
```

It connects these runtime components:

```text
SharedBuffer
  -> result_queue / latest observation
  -> ControlLoop.tick()
  -> SafetyGuard.filter_action()
  -> ControlCommand
  -> Pi05VlaDeployNode publisher
```

## 2. Source location

Implementation:

```text
pi05/deploy/src/pi05/deploy/runtime/control_loop.py
```

Main method:

```python
def tick(self) -> ControlCommand | None:
    """Return the next safe command without waiting for model inference."""
```

The phrase "without waiting for model inference" is the key design point. `tick()` must keep the robot control loop responsive even if the VLA model is slower than the control rate.

## 3. High-level responsibility

`tick()` does not run the neural network directly.

Instead, it does five orchestration jobs:

1. collect the newest finished `ActionChunk` from the inference worker;
2. activate or switch action chunks when needed;
3. submit a new asynchronous inference request before the current chunk runs out;
4. choose the next raw 14D action vector;
5. pass that action through `SafetyGuard` and return a safe `ControlCommand`.

So `tick()` is not a model function. It is a real-time control scheduler.

## 4. Exact execution sequence

The method body follows this order:

```text
1. now = time.monotonic()
2. _collect_result(now)
3. if active_chunk is None: _activate_pending(now, immediate=True)
4. _maybe_submit_request(now)
5. raw_action = _next_raw_action(now)
6. if raw_action is None: fallback
7. latest observation = shared_buffer.latest_observation(...)
8. SafetyGuard.filter_action(raw_action, observation, previous_action)
9. if rejected: fallback
10. update last_command
11. record published action
12. return ControlCommand(action=result.action)
```

## 5. Step-by-step notes

### 5.1 Collect finished inference result

```python
self._collect_result(now)
```

This checks `result_queue`, which is usually `SharedBuffer.chunk_result_queue`.

If the inference worker has produced a new `ActionChunk`, `_collect_result()` validates it with:

```python
is_action_chunk_usable(...)
```

Validation checks:

- action tensor rank is 2;
- action dimension matches `action_dim`, normally 14;
- all values are finite;
- chunk is not too old;
- time-aligned index is not too close to the end of the chunk.

If valid, it becomes `pending_chunk`.

### 5.2 Activate a pending chunk if there is no active chunk

```python
if self.active_chunk is None:
    self._activate_pending(now, immediate=True)
```

When the loop has no current chunk, it tries to promote `pending_chunk` into `active_chunk`.

The cursor is not always set to 0. It is set using:

```python
aligned = pending_chunk.aligned_index(now)
```

This aligns the action index with wall-clock time so the robot does not start executing an old chunk from the beginning.

### 5.3 Submit inference request before actions run out

```python
self._maybe_submit_request(now)
```

This is the prefetch mechanism.

If the active chunk cursor reaches:

```text
execute_horizon - prefetch_steps
```

then the loop submits a new `InferenceRequest` into `request_queue`.

With common values:

```text
execute_horizon = 10
prefetch_steps = 5
```

The request is triggered around cursor 5. At 30 Hz, that gives the inference worker roughly 5 control ticks, about 167 ms, to prepare the next chunk.

### 5.4 Pick the next raw action

```python
raw_action = self._next_raw_action(now)
```

This returns one raw 14D action vector.

It can come from:

- the current `active_chunk`;
- a blend between the previous executed command and the next chunk;
- a newly switched chunk.

If there is no usable action, `tick()` enters fallback.

### 5.5 Safety filtering

```python
result = self.safety_guard.filter_action(
    raw_action,
    observation=observation,
    previous_action=self.last_command,
)
```

The safety guard is the last gate before publishing.

It checks and adjusts the raw action through rules such as:

- finite-value check;
- action shape validation;
- arm joint delta clamp;
- optional joint limits;
- hand command clamp;
- fallback anchor from previous action or current observation.

Only accepted actions become `ControlCommand`.

### 5.6 Fallback

Fallback is used when:

- no active action is available;
- safety guard rejects the action;
- the current chunk is invalid or stale;
- observation is unavailable when submitting inference request.

The configured `fallback_policy` controls behavior:

```text
safe_stop
hold_last_action
continue_old_chunk
```

In the default `hold_last_action` style, the loop tries to re-validate and reuse `last_command`.

## 6. Important state fields

`tick()` depends on these internal fields:

| Field | Meaning |
|---|---|
| `active_chunk` | currently consumed `ActionChunk` |
| `pending_chunk` | newest valid chunk waiting to be activated |
| `active_cursor` | current step index inside `active_chunk` |
| `last_command` | last accepted safe `BimanualAction` |
| `request_pending` | whether an inference request is already in flight |
| `blend_active` | whether chunk boundary blending is running |
| `blend_counter` | current step inside the blend window |
| `next_chunk` | target chunk during blending |
| `next_cursor` | cursor inside `next_chunk` |
| `request_id` | monotonically increasing inference request id |

## 7. Relationship with SharedBuffer

`tick()` uses `SharedBuffer` in three ways:

```text
1. Pull finished action chunks:
   result_queue.get_latest_or_none()

2. Read latest observation:
   shared_buffer.latest_observation(max_age_s=...)

3. Record runtime metrics:
   record_inference_request()
   record_published_action()
   record_rejected_action()
   record_fallback()
   record_chunk_switch()
   record_discarded_chunk()
```

`SharedBuffer` is the thread-safe shared state. `tick()` is the high-frequency consumer and scheduler.

## 8. Why `tick()` must not block

The model inference loop may run at 10 Hz, while control runs at 30 Hz.

If `tick()` waited for model inference, robot control would stall. Therefore the design separates:

```text
ControlLoop.tick()       -> fast, deterministic, 30 Hz
InferenceWorker.run()    -> slower, asynchronous, around 10 Hz
```

`tick()` consumes already available chunks and asks for future chunks early.

## 9. Mental model

Think of `tick()` as a conductor in an orchestra:

```text
ObservationCollector gives it the latest sensory context.
InferenceWorker prepares future action sheets.
SharedBuffer places those sheets on the stand.
ControlLoop.tick() points to the next note every 33 ms.
SafetyGuard checks whether the note is safe to play.
Publisher sends the final command to hardware.
```

The key idea is:

```text
`tick()` does not think slowly. It schedules fast.
```

## 10. Minimal pseudocode

```python
def tick():
    now = monotonic_time()

    collect_latest_finished_chunk()

    if no_active_chunk:
        activate_pending_chunk_time_aligned()

    maybe_submit_async_inference_request()

    raw_action = get_next_action_or_blended_action()
    if raw_action is None:
        return fallback()

    observation = latest_fresh_observation()
    safe_result = safety_guard.filter_action(raw_action, observation, last_command)

    if not safe_result.accepted:
        return fallback()

    last_command = safe_result.action
    return ControlCommand(action=last_command)
```

## 11. Common confusion

### Is `tick()` the same as inference?

No. It does not call model forward directly. It only submits requests and consumes completed chunks.

### Does `tick()` publish ROS messages?

Not directly. It returns `ControlCommand`. The ROS node publishes the command.

### Does `tick()` always return an action?

No. It may return `None` when fallback policy is `safe_stop` or no safe command is available.

### Why does it use `aligned_index()`?

Because an action chunk is tied to the observation time. If the chunk becomes ready late, execution should jump to the time-aligned action index instead of replaying stale early actions.

## 12. One-sentence summary

`ControlLoop.tick()` is the 30 Hz real-time scheduler that turns asynchronous VLA `ActionChunk`s into one safe robot command per control frame.
