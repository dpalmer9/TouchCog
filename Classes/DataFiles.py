# Shared output-path helpers for protocol and survey data files

import pathlib
import re

DATA_FOLDER = pathlib.Path.home() / 'Documents' / 'TouchCog' / 'Data'


def sanitize_participant_id(participant_id):
	return re.sub(r'[^\w\-]', '_', str(participant_id).strip()) or 'Default'


def next_free_path(make_path, start=1):
	# Returns (index, path) for the first index >= start whose path does not exist yet
	index = start
	path = make_path(index)
	while path.exists():
		index += 1
		path = make_path(index)
	return index, path
