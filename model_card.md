# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**

---

## 2. Goal / Task and Intended Use  

**Goal:** VibeFinder tries to guess which songs a user will enjoy right now. It suggests the top 5 songs from a small catalog, with a reason for each one.

The user gives a favorite genre, a mood, an energy level, how happy they want songs to sound, and whether they like acoustic music. It assumes the user knows their taste and can describe it with these few settings.

**Intended use:**
- Classroom learning about how recommenders work.
- Trying out different taste profiles and seeing how scoring rules change the results.

**Not intended for:**
- Real users or a real music app. The catalog is only 23 songs.
- Learning a user's taste over time. It has no listening history.
- Making decisions about people (for example, guessing someone's personality or mood from their music).
- Judging which genres or artists are "better". Scores only show how well a song matches one profile.

---

## 3. Algorithm Summary  

Every song gets a score. The higher the score, the better the match.

- **Genre:** +2.0 points if the song's genre is the user's favorite.
- **Mood:** +1.5 points if the song's mood matches.
- **Energy:** up to +1.5 points. The closer the song's energy is to what the user wants, the more points.
- **Happiness (valence):** up to +1.0 point, the same "closer is better" idea.
- **Acoustic sound:** up to +0.5 points. Acoustic fans get points for acoustic songs, and others get points for electronic songs.

The best possible score is 6.5. The program scores every song, sorts them from highest to lowest, and shows the top 5 with the reasons for each score.

**Advanced features (Challenge 1):** songs also have popularity, release decade, mood tags, how instrumental they are, and an explicit flag. If a user sets these preferences, a song can earn up to 2.5 more points (max 9.0), and explicit songs lose 1.0 point if the user does not allow them. If the user does not set them, nothing changes.

**Changes from the starter:** I wrote the scoring and ranking logic, added valence and acousticness to the score, and made every recommendation explain its points.

---

## 4. Data Used  

- 23 songs in `data/songs.csv`.
- 15 genres: pop, lofi, rock, edm, metal, hip hop, classical, ambient, jazz, synthwave, indie pop, r&b, country, folk and reggae.
- 14 moods, including happy, chill, intense, melancholy, moody, angry and romantic.
- Most genres have only 1 or 2 songs. Pop and lofi have the most (3 each).
- Each song also has popularity (0 to 100), release decade, 1 or 2 mood tags, instrumentalness (0 to 1) and an explicit flag. I made up these values, since the songs are fictional.
- Missing: lyrics, language, artist popularity, release year, and many genres (k-pop, latin, blues and more).

---

## 5. Strengths  

- Works well for users whose taste matches the catalog. *Happy Pop*, *Intense Rock* and *Chill Lofi* all got the right songs at #1 (scores 6.40 or higher out of 6.5).
- "Closer is better" scoring makes sense: a user who wants calm music gets calm songs, not just the quietest ones.
- Every score comes with reasons, so it is easy to see *why* a song was picked.

---

## 6. Observed Behavior / Biases 

**Main weakness: sad listeners are underserved.** Only 4 of the 23 songs sound clearly sad (valence below 0.4), and two of those are loud metal songs. So a user who wants sad music has very few good options, and the scoring fills the rest of their list with happy songs that just match their genre or energy. For example, the Sad Raver profile (high energy, sad) got two happy EDM songs at the top, because a genre match (+2.0) is worth more than a mood match (+1.5). This is a filter bubble: users with "common" tastes (happy, upbeat) get great matches, while users with less common tastes get pushed toward what the catalog has most of.

Other weaknesses:

- **Energy gap treats users differently.** A user who wants medium energy (0.5) is never more than 0.5 away from any song, so every song gets at least 0.75 energy points and energy barely separates songs. A user who wants very high or very low energy sees a much bigger spread. Also, only 1 song (Velvet Hours, 0.55) sits in the middle range, so medium-energy users have few close matches.
- **Uneven catalog.** Most genres have only 1 or 2 songs. Rock has 1, so a rock fan gets non-rock songs from #2 down.
- **Exact text only.** "Pop" does not match "pop", and "indie pop" gets no credit for being close to "pop".
- **No input checks.** An energy of 1.5 is accepted, and larger values could give negative points.
- **Ignores** tempo, danceability, lyrics and listening history, and does not check variety (same artist can appear several times).

---

## 7. Evaluation Process  

### Profiles tested

*Note: the numbers in this section were measured with the 5 core features, before the advanced features were added. After adding them, Happy Pop's Gym Hero problem is mostly fixed: it is explicit and has no matching mood tags, so it drops from #3 to #5. The edge-case profiles do not use advanced preferences, so their results did not change.*

- **Normal:** Happy Pop, Intense Rock, Chill Lofi.
- **Tricky:** Sad Raver (high energy + sad), Unknown Genre (k-pop), Case Mismatch ("Pop"/"Happy"), Out-of-Range Energy (1.5), Sad Acoustic Pop.

I checked whether the top songs made sense and whether the reasons explained the scores. I also ran 2 automated tests with `pytest`, and both pass.

**What surprised me:**
- A capital letter ("Pop") quietly broke genre and mood matching, and a hip hop song made the top 5.
- The program never crashed on strange input. It just gave confident, wrong-feeling results.
- Gym Hero showed up in 4 of the 8 lists.

### Why does "Gym Hero" show up for Happy Pop fans?

Gym Hero is a loud workout song with an "intense" mood, not a "happy" one. But the program does not listen to the song. It only checks labels and numbers:

- Its genre label is "pop", which is worth the most points (+2.0).
- It is high energy (0.93) and fairly bright-sounding (valence 0.77), close to what a Happy Pop fan asked for.
- The only thing "wrong" is the mood, and missing the mood only costs 1.5 points.

So it beats Rooftop Lights, a happy indie pop song that feels like a better fit, because "indie pop" does not count as "pop". The program trusts the genre label more than the feeling of the song.

### Why Sunrise City ranked #1 for Happy Pop

| Feature | Song vs. user | Points |
|---|---|---|
| Genre | pop = pop | +2.00 |
| Mood | happy = happy | +1.50 |
| Energy | 0.82 vs 0.8 | +1.47 |
| Valence | 0.84 vs 0.8 | +0.96 |
| Acousticness | 0.18 vs 0.2 | +0.49 |
| **Total** | | **6.42 / 6.5** |

It matches both genre and mood, and its numbers are almost exactly what the user asked for. Golden Hour Crush also matches both, but its energy (0.72) is further from 0.8, so it comes second. Overall the Happy Pop list feels right, except Gym Hero at #3.

### Comparing profiles

- **Happy Pop vs. Chill Lofi:** Happy Pop gets bright, high-energy, electronic songs (Sunrise City, energy 0.82). Chill Lofi gets soft, slow, acoustic songs (Library Rain, energy 0.35). This makes sense: the two users asked for opposite energy and acoustic levels, and no song appears in both lists.
- **Happy Pop vs. Intense Rock:** Both want high energy, so Gym Hero shows up in both. But Intense Rock gets darker songs (Storm Runner, Pit Storm) because it asked for a lower valence and the "intense" mood. Same energy, different feeling.
- **Intense Rock vs. Chill Lofi:** Complete opposites. Rock gets loud, electric songs (energy 0.9+); lofi gets quiet, acoustic ones (energy around 0.35). This shows energy and acousticness are doing their job.
- **Intense Rock vs. Sad Raver:** Both want energy around 0.9, but Sad Raver gets happy EDM at the top because its genre is EDM. Its sad mood only pulls in quiet sad folk/classical songs at #3 and #4, which have the wrong energy. Neither list gives "loud and sad" well, because the catalog barely has those songs.
- **Happy Pop vs. Unknown Genre (k-pop):** Very similar songs (Golden Hour Crush, Rooftop Lights, Sunrise City), but scores are about 2 points lower because no song can match "k-pop". Makes sense: the system falls back to mood and energy.
- **Happy Pop vs. Case Mismatch:** Same wishes, but written "Pop"/"Happy". The list looks similar, yet scores drop to under 3 and a hip hop song sneaks in, because genre and mood never match. This is a bug, not a real difference in taste.
- **Happy Pop vs. Sad Acoustic Pop:** Same genre, opposite feeling. Sad Acoustic Pop gets sad folk and classical songs (Paper Boats, Winter Strings) first, and the happy pop songs fall to #3 to #5. This makes sense: the user's mood, valence and acoustic wishes together outweigh the genre.
- **Intense Rock vs. Out-of-Range Energy (1.5):** Both want loud music. The 1.5 user still gets loud metal and rock, but every song loses energy points, so scores are lower. The ranking looks fine only by luck; there is no check on the input.

### Experiment: double energy, halve genre

I changed energy from 1.5 to 3.0 and genre from 2.0 to 1.0 (new max score 7.0), re-ran all profiles, then put the original weights back. I checked the math by hand: Sunrise City = 1.0 + 1.5 + 2.94 + 0.96 + 0.49 = 6.89, which matched the output.

| Profile | Before | After | Better or just different? |
|---|---|---|---|
| Happy Pop | Gym Hero #3 | Gym Hero #5, Rooftop Lights #3 | **Better.** The happy song moved above the intense one. |
| Chill Lofi | Focus Flow #3 | Spacewalk Thoughts (ambient, chill) #3 | Different. Both fit. |
| Sad Raver | Sad songs at #3 and #4 | Sad songs gone; replaced by loud metal/rock | **Worse.** Energy now drowns out the sad mood. |
| Sad Acoustic Pop | Pop songs at #3 to #5 | Pop songs gone; calm ambient, lofi and classical songs | Different. Fits the feeling, ignores the genre. |

**Conclusion:** the change made results *different*, not clearly *more accurate*. It fixed the Gym Hero problem, but it made energy the main thing, so a high-energy user now gets loud songs no matter what mood they want. This shows the results are very sensitive to the weights, and there is no single "right" setting for every user.

---

## 8. Ideas for Improvement  

1. **Smarter matching.** Ignore capital letters, and give partial credit to similar genres (pop and indie pop) and moods (sad and melancholy). This would fix the Case Mismatch bug and stop Gym Hero beating Rooftop Lights.
2. **A bigger, more balanced catalog.** Add more songs, especially sad songs and more songs per genre, so less common tastes get good matches too.
3. **More variety in the top 5.** Limit songs per artist and check that numbers are between 0 and 1.

---

## 9. Personal Reflection  

**Biggest learning moment:** lowering the genre weight. One number change flipped the Sad Raver results from happy EDM to sad folk songs. I learned that a recommender is mostly a set of choices about what matters and how much, and there is no single setting that is right for every user.

**How AI tools helped, and when I double-checked:** I used Claude as a coding assistant. It helped me write the scoring code, come up with tricky test profiles, and run experiments quickly. But I had to check its work several times:
- My README described 5 features, but the code only used 3. They did not match until I noticed and fixed it.
- The starter tests passed even though the `Recommender` class was still a placeholder. Passing tests did not mean the code worked.
- During the weight experiment, both runs first printed the same results because Python reused an old cached file. If I had not compared the scores by hand, I would have reported the wrong conclusion.

**What surprised me:** the algorithm is just adding up points, but the results still *feel* like real recommendations. Library Rain for a lofi fan feels personal. It also fails in quiet ways: it never crashes, it just confidently gives happy songs to a sad user or breaks because of a capital letter.

**What I would try next:** let users like more than one genre, learn from songs they skip or replay, and add a "surprise me" slot so the top 5 is not always the same kind of song.
