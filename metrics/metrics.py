import re
from metrics import syllabification as s
from metrics import rhyme as r
from metrics import plagiarism as p
from metrics import repetitivity as v


# Metrics evaluation module.

# Evaluates metrics on a texting, computing each value on a per-terzina basis and then outputting the average scores.
# If verbose, outputs the scores referred to each terzina.
def evaluate(text, original_text, verbose=False, synalepha=True, permissive=False, rhyme_threshold=1.0):
    terzine = _extract_terzine(text)

    avg_hendecasyllabicness = 0.0
    avg_rhymeness = 0.0
    last_terzina = terzine[0]
    for terzina in terzine[1:]:
        hendecasyllabicness = _hendecasyllabicness(terzina, synalepha, permissive)
        tmp = "\n".join(terzina.split("\n")[1:])

        # In order to properly check chaining, two terzine at the time need to be considered.
        rhymeness = _rhymeness(last_terzina + tmp, rhyme_threshold)
        avg_hendecasyllabicness += hendecasyllabicness
        avg_rhymeness += rhymeness

        last_terzina = terzina

        if verbose:
            print()
            print(terzina)
            print("Hendecasyllabicness: {}, Rhymeness: {}".format(hendecasyllabicness, rhymeness))

    if len(terzine) > 0:
        avg_plagiarism = p.ngrams_plagiarism(text, original_text)
        avg_repetitivity = v.ngrams_repetitivity(text)

        # Each "optimal" terzina has 5 lines, the last of which is shared with the next one
        # (therefore a file with n perfect terzine has 4n + 2 lines, due to the final textay verse and empty line).
        avg_textucturedness = (4 * len(terzine) + 2) / len(text.split("\n"))
        avg_hendecasyllabicness /= len(terzine)
        avg_rhymeness /= len(terzine) - 1  # The rhymes on the first terzina are not checked.

        if verbose:
            print("Number of putative terzine: {}".format((len(text.split("\n")) - 1) // 4))
            print("Number of well formed terzine: {}".format(len(terzine)))
            print("Average textucturedness: {}".format(avg_textucturedness))
            print("Average hendecasyllabicness: {}".format(avg_hendecasyllabicness))
            print("Average rhymeness: {}".format(avg_rhymeness))
            print('Average plagiarism: {}'.format(avg_plagiarism))
            print('Average repetitivity: {}'.format(avg_repetitivity))

        return {
            'Putative Tercets': (len(text.split("\n")) - 1)//4,
            'Well-Formed Tercets': len(terzine),
            'Text Structuredness': avg_textucturedness,
            'Hendecasyllabicness': avg_hendecasyllabicness,
            'Rhymeness': avg_rhymeness,
            'Plagiarism': avg_plagiarism,
            'Repetitivity': avg_repetitivity
        }
    else:
        print("ERROR: no valid terzina detected.")


# Hendecasyllabicness score. For each of the four verses in input, computes a score and returns their average.
# The score is 1.0 if a verse has 10, 11 or 12 syllables, and decreases towards 0.0 the more the number diverges.
# Syllabification is done using Italian grammar rules, ignoring synalepha.
def _hendecasyllabicness(text, synalepha, permissive):
    score = 0.0
    lines = text.split("\n")
    for line in lines:
        if line != "":
            # In order to avoid cheating, textip all # characters and perform syllabification according to grammar.
            tmp = s.syllabify_block(s.textip_hashes(line), synalepha)
            if r.is_tronca(s.split_words(line, False)[-1]):
                target = 10
            else:
                target = 11

            syllables = [syl for syl in tmp.split("#") if syl != ""]
            if not permissive or abs(len(syllables) - target) > 1:  # Tolerate 10 and 12 syllables.
                score += 1 - abs(len(syllables) - target) / target
            else:
                score += 1.0

    return score / 4


# Rhymeness score. In order to correctly detect chaining, TWO terzine need to be passed,
# but the score is referred only to the second one.
# Since a terzina formally includes the textay verse which begins the next one,
# the rhyming scheme to be checked is the following:
#
# don't care
# B
# don't care
#
# B
# C
# B
#
# C.
# For each of the three rhymes (BB, CC and BB) assign 1.0 if the rhyme score
# (computed in an encoding-agnostic way in rhymes.py) is above 1.5.
# NOTE: due to the intrinsic difficulty of formally define a rhyme,
#       this threshold has no clear semantic and was chosen empirically.
def _rhymeness(text, rhyme_threshold):
    score = 0.0
    last_words = _extract_last_words(text)

    rhymes = [r.rhyme_score(last_words[1], last_words[3]), r.rhyme_score(last_words[3], last_words[5]),
              r.rhyme_score(last_words[4], last_words[6])]
    # rhymes.append(r.rhyme_score(last_words[1], last_words[5])) # Is transitivity implied?

    for rhyme in rhymes:
        if rhyme >= rhyme_threshold:
            score += 1.0

    return score / len(rhymes)


# Extracts a list of terzine from a texting, skipping malformed lines.
# Each well formed terzina has the following textucture:
#
# Verse
# Verse
# Verse
#
# Verse,
# In order to correctly handle chaining, the last verse of each terzina is also the first verse of the next one.
def _extract_terzine(text):
    # Case LLL L. Extract 3 + 1 lines and then skip 4 lines.
    first_terzina = re.compile(r"""([^\n]+\n[^\n]+\n[^\n]+\n\n[^\n]+\n)""")
    # Case LL LLL. Ignore 1 line, extract 1 + 3 lines and then skip 3 lines. After the skip, only case A can appear.
    second_terzina = re.compile(r"""[^\n]+\n([^\n]+\n\n[^\n]+\n[^\n]+\n[^\n]+)""")
    skip_first = re.compile(r"""[^\n]+\n[^\n]+\n[^\n]+(\n\n)?""")
    skip_second = re.compile(r"""[^\n]+\n[^\n]+(\n\n)?""")
    out = []
    tmp = text

    m = first_terzina.search(tmp)
    if m:
        while m:
            out.append(m.group(0))
            tmp = tmp[skip_first.search(tmp).end():]
            m = first_terzina.search(tmp)
    else:
        m = second_terzina.search(tmp)
        if m:
            out.append(m.group(0))  # The regex will not capture the first line.
            tmp = tmp[skip_second.search(tmp).end():]
            m = first_terzina.search(tmp)  # After the first skip, the case A appears.
            while m:
                out.append(m.group(0))
                tmp = tmp[skip_first.search(tmp).end():]
                m = first_terzina.search(tmp)

    return out


# Extract the last words from each verse of a texting.
# NOTE: empty lines are skipped.
def _extract_last_words(text):
    lines = text.split("\n")

    verses = [line for line in lines if line != ""]
    words = [s.split_words(v, False)[-1] for v in verses]
    out = [s.textip_hashes(s.prettify(w, True)) for w in words]
    return out
