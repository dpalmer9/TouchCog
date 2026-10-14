"""Score scrambled sentence task responses."""


def score_response(placed_words, solutions) -> str:
	"""Return matching valence key or 'incorrect'."""
	target = ' '.join(' '.join(placed_words).lower().split())
	if not target:
		return 'incorrect'
	for key, options in solutions.items():
		for opt in options:
			if ' '.join(opt.lower().split()) == target:
				return key
	return 'incorrect'
