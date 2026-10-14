# v0.4.0 rounds before the release

v0.4.0 went through three correction rounds before its released batches. These runs are kept because they are what exposed the problems; none of their numbers are the released results.

## Round 1: GPT-5.4 (`runs-gpt-54/`)

Validator clean was 29 percent. Most failures were the validator being stricter than the design intended: it rejected STRIDE coverage of pairs beyond the required set (34 runs), treated a missing category on a finding as an error when it is bookkeeping (28), and rejected elements that listed their own id (13). The baseline held out runs were also misjudged because the new coverage rule was applied to documents from an older schema. Fixed in corrections 1 and 2, which also added the "below the floor" error, the approval volume threshold, and the property finding precedence rule.

## Round 2: GPT-5.4 (`runs-gpt-54-round2/`) and Claude (`runs-claude-round2/`)

GPT-5.4 reached 85 percent validator clean and passed criteria 1 to 3. Claude passed criterion 4 everywhere but reported a false positive in all 6 runs of the clean and forecast only designs: property findings rating a missing audit trail on read only Q&A agents `moderate`. Both models also missed ASI03 on case 12. Fixed in corrections 3: rubric 0.3.1 rates a missing property above `low` only when an affected capability is consequential, and the skill tags agents acting with a person's credentials as ASI03.

Case 12's expected file was also corrected once, in corrections 2, to accept ASI10 alongside ASI03 (the crosswalk maps repudiation to ASI10) and common phrasings of the engineer's token. That correction applies to every version's runs when scored.
