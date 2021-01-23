from metrics.text_encoder import Tokenizer

def ngrams_repetitivity(text, n=4):
    # the tokenizer is used to remove non-alphanumeric symbols
    tokenizer = Tokenizer()
    tokenized_text = tokenizer.tokenize(text.lower())

    total_ngrams = len(tokenized_text) - n + 1
    repetitions_counter = 0

    for i in range(total_ngrams):
        ngram = tokenizer.join(tokenized_text[i:i+n])
        remaining_text = tokenizer.join(tokenized_text[:i]) + ' ' + tokenizer.join(tokenized_text[i+n:])
        repetitions_counter += 1 if ngram in remaining_text else 0
    return 1 - (repetitions_counter / total_ngrams)
