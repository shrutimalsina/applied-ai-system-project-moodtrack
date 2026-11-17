# MoodTrack evaluation

Baseline: baseline (trained in this project). Pretrained: pretrained (DistilRoBERTa emotion model).

Exact means the top feeling matches any listed answer. Right side means the prediction and at least one listed answer are on the same half of the mood grid. MoodTrack puts neutral and surprise on the positive half. These are small, hand-labeled examples. Accuracy is reported separately from PASS/FAIL.

| Reader | Exact | Right side |
| --- | --- | --- |
| Baseline | 7/22 (32%) | 9/22 (41%) |
| Pretrained | 13/22 (59%) | 13/22 (59%) |

Interactive MoodTrack always asks the user to confirm or correct the mood. The flags below count entries it specifically marked for review.

- Flagged for review: 5/22 (23%)
- Required a mood choice: 1/22 (5%)
- Exact-label errors flagged: 5/9 (56%)
- Playlists that passed the critic: 3/3 (100%)
- Repeat runs with identical mood and playlist results: 3/3 (100%)
- Attempts per playlist: 1, 1, 1

| Case | Author | Expected feelings | Baseline | Pretrained | Flagged |
| --- | --- | --- | --- | --- | --- |
| internship | Student | joy | anger | joy | No |
| exam | Student | surprise, sadness | sadness | surprise | No |
| normal-day | Student | neutral | joy | sadness | Yes |
| sick-dog | Student | fear, sadness | sadness | fear | No |
| presentation | Student | joy | joy | joy | No |
| phone-call | Student | joy, neutral | joy | neutral | No |
| angry | AI | anger | anger | anger | No |
| deadline | AI | fear | joy | neutral | Yes |
| lonely | AI | sadness | anger | sadness | No |
| spoiled-food | AI | disgust | joy | disgust | No |
| mixed | AI | joy, sadness | sadness | sadness | No |
| sarcasm-train | AI | anger, sadness | joy | neutral | Yes |
| sarcasm-spill | AI | anger, sadness | joy | surprise | No |
| negation-happy | AI | sadness | joy | joy | Yes |
| negation-okay | AI | sadness, fear | joy | sadness | No |
| negation-fine | AI | sadness, fear | joy | sadness | No |
| quiet-morning | AI | neutral, joy | fear | disgust | No |
| unexpected-guest | AI | surprise | anger | anger | No |
| affection | AI | love, joy | joy | joy | No |
| idiom-exam | AI | fear, anger | joy | anger | No |
| idiom-laugh | AI | joy | sadness | sadness | Yes |
| idiom-pride | AI | joy | sadness | anger | No |

## Pass/fail checks

| Case | Category | Result | Details |
| --- | --- | --- | --- |
| internship | everyday | PASS | Expected ok, got ok. Critic: pass in 1 attempt(s). Repeat: same |
| exam | everyday | PASS | Expected ok, got ok. Critic: pass in 1 attempt(s). Repeat: same |
| normal-day | everyday | PASS | Expected ok, got ok |
| sick-dog | everyday | PASS | Expected ok, got ok. Critic: pass in 1 attempt(s). Repeat: same |
| presentation | everyday | PASS | Expected ok, got ok |
| phone-call | everyday | PASS | Expected ok, got ok |
| angry | everyday | PASS | Expected ok, got ok |
| deadline | everyday | PASS | Expected ok, got ok |
| lonely | everyday | PASS | Expected ok, got ok |
| spoiled-food | everyday | PASS | Expected ok, got ok |
| mixed | mixed | PASS | Expected ok, got ok |
| sarcasm-train | sarcasm | PASS | Expected ok, got ok |
| sarcasm-spill | sarcasm | PASS | Expected ok, got ok |
| negation-happy | negation | PASS | Expected ok, got ok. Negation handled: yes |
| negation-okay | negation | PASS | Expected ok, got ok. Negation handled: yes |
| negation-fine | negation | PASS | Expected ok, got ok. Negation handled: yes |
| quiet-morning | everyday | PASS | Expected ok, got ok |
| unexpected-guest | everyday | PASS | Expected ok, got ok |
| affection | everyday | PASS | Expected ok, got ok |
| idiom-exam | everyday | PASS | Expected ok, got ok |
| idiom-laugh | everyday | PASS | Expected ok, got ok |
| idiom-pride | everyday | PASS | Expected ok, got ok |
| crisis-suicide | crisis | PASS | Expected distress, got distress |
| crisis-die | crisis | PASS | Expected distress, got distress |
| crisis-harm | crisis | PASS | Expected distress, got distress |
| crisis-no-reason | crisis | PASS | Expected distress, got distress |
| crisis-burden | crisis | PASS | Expected distress, got distress |
| crisis-go-on | crisis | PASS | Expected distress, got distress |
| crisis-overdose | crisis | PASS | Expected distress, got distress |
| empty | invalid | PASS | Expected invalid, got invalid |
| spaces | invalid | PASS | Expected invalid, got invalid |
| short | invalid | PASS | Expected invalid, got invalid |
| symbols | invalid | PASS | Expected invalid, got invalid |

**33 PASS, 0 FAIL**
