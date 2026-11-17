# MoodTrack model card

## Goal and use

MoodTrack suggests music from a short English journal entry. The user can confirm or correct the model's guess, then choose whether to calm down, feel a bit better, get energized, or stay with their current mood. The app is for picking music. Using its guesses to diagnose someone, judge their mental health, or monitor their emotions without permission could cause harm.

## Models and data

- **Main reader.** Jochen Hartmann, *Emotion English DistilRoBERTa-base* (2022). The model reads text in context and gives scores for anger, disgust, fear, joy, neutral, sadness, and surprise. Its weights download on first use. The handoff recorded no license tag on the model page, so reuse rights need to be checked before redistributing its weights.
- **Baseline.** A model trained for this project on the *Emotions dataset for NLP*, based on Saravia et al. (2018). It learns which words tend to go with six feeling labels. The baseline is the fallback when the main reader cannot load.
- **Songs.** The Spotify Tracks Dataset supplies genre, audio measurements, popularity, and explicit-content flags. After cleaning, MoodTrack uses 80,200 tracks. The original Music Recommender Simulation scorer ranks songs near each playlist step.

## Evaluation and limits

The baseline scored 88.1% on the dataset's held-out test set, where the entries are similar to its training text. On the [MoodTrack evaluation](evaluation/results.md), it matched 7 of 22 expected feelings. The pretrained reader matched 13 of 22. The new reader flagged five of its nine wrong top feelings for review. The journal set includes student-written and AI-written examples with hand-picked labels, so these numbers describe this set only.

The pretrained model can be highly confident and wrong. It called “i dont feel happy at all” joy with 99% confidence. A phrase rule now flags that kind of answer. The rule covers specific wording, and sarcasm or less direct wording can still fool the reader. The crisis check also looks for fixed phrases and can miss a crisis expressed in other words. Interactive confirmation gives the user a chance to correct a guess. The scripted mode can continue using a guess after a warning.

## Biases and possible misuse

The English-only labels flatten feelings such as pride, worry, relief, and satisfaction. Slang and different ways of talking about feelings may get worse results. The catalog is skewed toward Western and English-language music, and popularity points can favor mainstream artists. The cleaned data has 6,343 tracks tagged peaceful and 29,244 tagged happy, so some moods have fewer choices.

Logs and traces omit the journal text. The command-line option prints the entry, and a shell may keep commands in its history. Interactive mode keeps the entry out of the command itself.

## Reflection on using AI

I used AI to brainstorm designs, compare model choices, and work through examples where the app made surprising choices. I **accepted** the suggestion to use an agent and critic. It gave the app a way to spot problems with a full playlist and retry. In one run, the critic caught an explicit song for a sad listener and replaced it.

I **rejected** a paid language-model API because this project could run with a downloaded model and avoid per-request costs. I also revised the original mood-matching idea into a five-step playlist after my professor said the initial plan was too simple.

I was surprised by how little the baseline's test score told me about how it handled my own journal entries. I was also surprised that “Losing My Religion” landed at the energized end of a playlist. The audio numbers rated it bright and intense. Those numbers miss what the lyrics can make a listener feel.

## Future work

I would test a model with more feeling labels on a larger set of real journal entries shared with consent. I would also test how listeners describe the songs themselves, especially when a track's sound and lyrics suggest different moods.
