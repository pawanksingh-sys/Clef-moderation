# Notes

## How to run the program

1. Copy `cloud-flare.sh` to `cloud-flare.local.sh` and put your Cloudflare account ID and Workers AI API token in it. This file is ignored by git, so the token is never committed.
2. First round: `python3 classify.py` classifies `comments.json` with `clef-flash` and writes `results.html` (and `results.json`).
3. Second round: `python3 classify.py v2` classifies `comments-v2.json` with `clef` and writes `results-v2.html` (and `results-v2.json`).
4. To view a page in Codespaces, run `python3 -m http.server 8000`, open the forwarded port in the browser and click the HTML file.

The program uses only the Python standard library. I used the same instructions and criteria for both rounds, so that the two results can be compared.

## Tools and models

I did the whole task on an iPad, using Safari and GitHub Codespaces, with Cloudflare Workers AI for the Clef models (`clef-flash` for the first round and `clef` for the second). I used Claude (Opus 5.5) to guide me through the setup, since I had not used GitHub, Codespaces or Cloudflare before, and to write the Python program.

For `MISTAKES.md` and `MISTAKES-v2.md`, I read every comment and made every label decision myself. On some hard cases I discussed with Claude how much weight to give to things like the local and cultural context, the course's definitions, and how I had labelled similar comments, before I made my decision. Claude did not give me its own view on a label until I had decided. After that I used it for a second opinion, to check that my labels were consistent with each other, and to turn my reasoning into tidy entries. Where I changed a label after that discussion, the final decision was still mine.

## What I noticed

- **Clef is good with obvious insults and weak with harm that has no rude words.** In the first round, all four of its mistakes (27, 69, 76, 83) were calm posts with no abusive words: gender and group stereotypes, and digs at a person. In the second round it read sarcasm literally (42) and missed a veiled threat (91). Posts with plain insults such as "idiot" were caught with high confidence.
- **Clef reacts to words, not to what the post does.** It labelled a student laughing at himself as toxic (v2 comment 7), and a student reporting a stereotype as toxic because she quoted it (v2 comment 20). Spam with a useful tip at the start got through as acceptable (v2 comment 23), and genuine student requests with promotional wording made it unsure (comment 89 in round one, comment 52 in round two).
- **The "check" flag works better with the larger model.** With `clef-flash`, two of the four mistakes were made with high confidence (27 at 0.71 and 69 at 0.87), so the flag would not have caught them. With `clef`, all six mistakes were flagged "check". If only one model can be used, I would use `clef` and send every flagged post to a human.
- **Some posts need urgent handling, not just a label.** The phishing post (v2 comment 40) and the post telling people where to find Nikita (v2 comment 91) can cause real harm outside the forum. They should probably have their own label or trigger an alert to staff, instead of sharing "spam" and "toxic" with ordinary rude posts and ads.
- **A few students write most of the hostile posts.** In the first file, Vikram Singh, Rahul Chauhan, Saurabh Yadav and Deepak Mishra wrote nearly all of them. In the second, Manav Jain, Rohit Chawla and Vishal Thakur did. Clef judges each post on its own, so it cannot see this, but a moderator would want to know who keeps doing it.
- **Hindi and Hinglish were labelled correctly but with low confidence** (v2 comments 19 and 83), so posts in Indian languages may need more human checking.
- **Three labels are not enough for some posts.** There is no place for "rude but not abusive", so mild posts have to go into toxic. Many students also write in their second or third language, so harsh wording is not always meant as harshly as it reads.
- **Possible improvements to the criteria:** say that a post can be toxic without abusive words (stereotypes, sarcasm, threats), that quoting abuse in order to report it is acceptable, that making fun of yourself is not toxic, and that asking for passwords or pushing paid offers is spam even when the tone is friendly.

## How it felt

I had never used GitHub, Codespaces or Cloudflare before, so the setup on my iPad was slow at first, and I lost my API token once and had to make a new one. Reading the comments was the part I enjoyed most. Some made me laugh and some genuinely annoyed me. Most of the hostile posts were clearly toxic, but a few could have been ordinary Indian college banter, and without knowing the people involved it was hard to say where teasing ends and bullying starts. I also had to watch my own habits, since I use some of the same emojis in a friendly way. By the second file I was noticing patterns, such as the same few students writing most of the hostile posts, and I think I would get much faster at this with practice.
