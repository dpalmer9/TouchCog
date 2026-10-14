import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scoring import score_response

emotional = {
	"positive": ["the future looks very bright"],
	"negative": ["the future looks very dismal"]
}

assert score_response(["the", "future", "looks", "very", "bright"], emotional) == "positive"
assert score_response(["the", "future", "looks", "very", "dismal"], emotional) == "negative"
assert score_response(["the", "weather", "is", "mild", "today"], {"neutral": ["the weather is mild today"]}) == "neutral"
assert score_response(["future", "the", "looks", "very", "bright"], emotional) == "incorrect"
assert score_response(["the", "future", "looks", "very", "cloudy"], emotional) == "incorrect"
assert score_response(["The", "Future", "LOOKS", "very", "bright"], emotional) == "positive"
assert score_response(["  the  ", " future", "looks ", "\tvery\t", "bright  "], emotional) == "positive"
assert score_response(["the", "future", "looks", "very", "dismal"], {"negative": ["  the   future   looks   very   dismal  "]}) == "negative"
assert score_response([], emotional) == "incorrect"

print('test_scoring OK')
