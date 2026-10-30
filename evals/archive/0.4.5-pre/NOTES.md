# v0.4.5 round before the release

`runs-gpt-54/` is the first GPT-5.4 batch on v0.4.5, run before two fixes. It is kept because it is what exposed them; its numbers are not the released results.

- First attempt validity was 68 percent, close to the 69 percent a rescoring of v0.4.4 runs had predicted.
- Two runs on case 02, the clean HR policy design, reported false positives: a missing audit record on a read only agent rated `moderate`. The consequence rule says such a finding is `low`, but the validator only warned. Earlier, unrelated structural controls had credited the finding down to `low` and hidden the mistake; once v0.4.5 stopped that credit, it surfaced. Fixed by making a wrong inherent tier on a property finding an error, and by stating that a reply to the authenticated requester is not egress.
- Rescoring older batches with the first build applied the new credit rules retroactively and changed published validity figures. Fixed by applying the new rules only to assessments made under rubric 0.3.3 or later.
