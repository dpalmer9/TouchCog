# Shared output-path helpers for protocol and survey data files
"""Shared output-path helpers for protocol and survey data files."""

import pathlib
import re

DATA_FOLDER = pathlib.Path.home() / 'Documents' / 'TouchCog' / 'Data'


def sanitize_participant_id(participant_id):
	"""Return a safe, filesystem-friendly participant identifier.

	Parameters
	----------
	participant_id : int or str
		The raw participant identifier supplied by the user.

	Returns
	-------
	str
		The identifier stripped of surrounding whitespace with every
		character outside ``[A-Za-z0-9_-]`` replaced by ``_``, or the
		string ``'Default'`` when the result would be empty.
	"""
	return re.sub(r'[^\w\-]', '_', str(participant_id).strip()) or 'Default'


def next_free_path(make_path, start=1):
	"""Return the first unused output path and its index.

	For each index beginning at ``start`` the caller's ``make_path``
	callback builds a candidate path; the first index whose path does
	not already exist is returned with that path.

	Parameters
	----------
	make_path : callable
		A function of a single integer index that returns the candidate
		``pathlib.Path`` for that index.
	start : int, optional
		First index to test. Defaults to 1.

	Returns
	-------
	tuple of (int, pathlib.Path)
		The first index at or above ``start`` whose path does not yet
		exist, together with that path.
	"""
	# Returns (index, path) for the first index >= start whose path does not exist yet
	index = start
	path = make_path(index)
	while path.exists():
		index += 1
		path = make_path(index)
	return index, path
