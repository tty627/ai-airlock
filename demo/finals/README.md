# Finals development demonstration

This is a **synthetic development example**. It is separate from the public
engineering acceptance cases in `benchmark/finals_cases.json`. Neither is a
blind holdout or a production dataset.

The demonstration starts a bounded evidence session, obtains initial evidence,
and executes two **scripted preset questions**. No LLM chooses the questions and
no final incident diagnosis is claimed. The emitted JSON is a real execution
trace, not a prerecorded successful response.

From the repository root:

```bash
python demo/finals/run_demo.py --backend lexical --output artifacts/finals-demo.json
python benchmark/run_finals_eval.py --backend lexical --output artifacts/finals-eval-lexical.json
```

After preparing the repository's pinned `intfloat/multilingual-e5-small`
OpenVINO export with `scripts/prepare_embedding_model.py`:

```bash
python demo/finals/run_demo.py --backend openvino --output artifacts/finals-demo-openvino.json
python benchmark/run_finals_eval.py --backend openvino --output artifacts/finals-eval-openvino.json
```

These commands use the configured/default model directory. For an export in a
different location, pass `--model-dir` with that directory to each command.
An unavailable OpenVINO backend fails; it never switches to lexical retrieval.
These commands do not prove that the machine is Intel Core Ultra, that a real
productivity host has integrated the Skill, or that raw files are isolated from
that host by operating-system permissions.

## What to inspect

- Initial evidence and the additional lines returned by the preset questions.
- Stable evidence references and pseudonyms within this session.
- Absence of the listed synthetic secret/email values in the released trace.
- Full serialized response size across **all** rounds, including metadata.
- Cases where preset questions return no new evidence or the task remains
  unanswerable. Missing evidence is not proof that no such evidence exists.

The acceptance runner compares raw full context, full-context redaction using
the same detectors, the initial session, and the session plus preset questions.
Evidence retention is exact source-specific marker presence, **not** root-cause
accuracy. The full-context baseline isolates detected instructions and redacts
PII but has no task-blocking policy. On small inputs, session protocol overhead
can cost more estimated tokens than simply providing all sanitized context.

No real credentials or customer data are included. `example.invalid` names and
the explicitly synthetic password are inert test data. Runtime reports should
be reviewed as evidence from the specific machine and backend that produced them.
